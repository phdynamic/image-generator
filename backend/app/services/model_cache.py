"""Helpers for the on-disk HuggingFace model cache."""
import shutil
from pathlib import Path

from ..config import settings

GIB = 1024 ** 3


def repo_dir(model_id: str) -> Path:
    return Path(settings.MODELS_CACHE_DIR) / ("models--" + model_id.replace("/", "--"))


def is_cached(model_id: str) -> bool:
    """True only for a finished download: files present and none still partial."""
    root = repo_dir(model_id)
    snapshots = root / "snapshots"
    try:
        if not snapshots.is_dir():
            return False
        if any((root / "blobs").glob("*.incomplete")):
            return False
        return any(p.is_file() for p in snapshots.rglob("*"))
    except OSError:
        return False


def cache_size(model_id: str) -> int:
    """Bytes on disk for this model, including a download in progress."""
    root = repo_dir(model_id)
    total = 0
    try:
        for path in root.rglob("*"):
            # Snapshot entries are symlinks to blobs on Linux; count real files once.
            if path.is_file() and not path.is_symlink():
                total += path.stat().st_size
    except OSError:
        pass
    return total


def free_disk_bytes() -> int:
    return shutil.disk_usage(settings.MODELS_CACHE_DIR).free


def delete(model_id: str) -> None:
    shutil.rmtree(repo_dir(model_id), ignore_errors=True)
