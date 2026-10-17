"""Downloads models in the background and reports progress.

Progress is measured from the cache folder's size on disk, so it works with
any diffusers / huggingface_hub version. One download runs at a time.
"""
import errno
import logging
import threading
from typing import Callable

from . import model_cache
from .hf_auth import gated_message, hf_token_available
from .model_registry import ModelSpec

logger = logging.getLogger(__name__)


class DownloadBusy(Exception):
    def __init__(self, active_model_id: str):
        super().__init__(active_model_id)
        self.active_model_id = active_model_id


def friendly_error(exc: Exception, model_id: str = "") -> str:
    name = exc.__class__.__name__
    text = str(exc)
    if isinstance(exc, OSError) and exc.errno == errno.ENOSPC:
        return "The disk is full. Free some space (or delete a model you don't use) and try again."
    if name in ("GatedRepoError", "RepositoryNotFoundError") or "401" in text or "gated" in text.lower():
        return gated_message(model_id, hf_token_available())
    return text[:300] or name


class DownloadManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._states: dict[str, dict] = {}
        self._active: str | None = None

    def active(self) -> str | None:
        with self._lock:
            return self._active

    def state(self, model_id: str) -> dict | None:
        """None when nothing is in flight or failed for this model."""
        with self._lock:
            state = self._states.get(model_id)
            state = dict(state) if state else None
        if state and state["status"] == "downloading":
            state["downloaded_bytes"] = model_cache.cache_size(model_id)
        return state

    def start(self, spec: ModelSpec, fetch: Callable[[ModelSpec], None]) -> None:
        with self._lock:
            if self._active:
                raise DownloadBusy(self._active)
            self._active = spec.id
            self._states[spec.id] = {
                "status": "downloading",
                "downloaded_bytes": 0,
                "total_bytes": int(spec.download_gb * model_cache.GIB) if spec.download_gb else None,
                "error": None,
            }
        threading.Thread(target=self._run, args=(spec, fetch), name=f"download-{spec.id}", daemon=True).start()

    def _run(self, spec: ModelSpec, fetch: Callable[[ModelSpec], None]) -> None:
        error = None
        try:
            fetch(spec)
        except Exception as exc:  # noqa: BLE001 - shown to the user
            logger.exception("Download of %s failed", spec.id)
            error = friendly_error(exc, spec.id)
        with self._lock:
            if error:
                self._states[spec.id].update(status="error", error=error)
            else:
                self._states.pop(spec.id, None)
            self._active = None

    def clear(self, model_id: str) -> None:
        with self._lock:
            if self._states.get(model_id, {}).get("status") == "error":
                del self._states[model_id]


download_manager = DownloadManager()
