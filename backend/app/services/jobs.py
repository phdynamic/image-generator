"""A tiny in-memory job queue.

Generating an image can take minutes (especially the first time a model loads).
Holding one HTTP request open that long breaks behind proxies such as
Cloudflare, which drop requests after ~100 seconds. Instead, the API accepts a
job instantly and the page polls for the result.
"""
import logging
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)

KEEP_FINISHED_SECONDS = 3600


class JobError(Exception):
    """Raised by a job function to report a user-facing failure."""

    def __init__(self, detail: str, status_code: int = 500):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


@dataclass
class Job:
    id: str
    fn: Callable[[], dict]
    status: str = "queued"  # queued | running | done | error
    result: dict | None = None
    error: str | None = None
    created: float = field(default_factory=time.time)
    finished: float | None = None


class JobManager:
    """Runs jobs one at a time, in order, on a single background thread."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._order: list[str] = []  # queued job ids, oldest first
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None

    def submit(self, fn: Callable[[], dict]) -> str:
        job = Job(id=uuid.uuid4().hex, fn=fn)
        with self._lock:
            self._prune()
            self._jobs[job.id] = job
            self._order.append(job.id)
            if self._worker is None or not self._worker.is_alive():
                self._worker = threading.Thread(target=self._run, name="job-worker", daemon=True)
                self._worker.start()
        self._queue.put(job.id)
        return job.id

    def queued_count(self) -> int:
        with self._lock:
            return len(self._order)

    def snapshot(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            data = {
                "id": job.id,
                "status": job.status,
                "queue_position": self._order.index(job.id) if job.id in self._order else 0,
                "image": job.result if job.status == "done" else None,
                "error": job.error,
            }
        return data

    def _run(self):
        while True:
            job_id = self._queue.get()
            with self._lock:
                job = self._jobs.get(job_id)
                if job is None:
                    continue
                job.status = "running"
                if job_id in self._order:
                    self._order.remove(job_id)
            try:
                result = job.fn()
                outcome = ("done", result, None)
            except JobError as exc:
                outcome = ("error", None, exc.detail)
            except Exception as exc:  # noqa: BLE001 - surface anything to the user
                logger.exception("Job %s failed", job_id)
                outcome = ("error", None, str(exc) or exc.__class__.__name__)
            with self._lock:
                job.status, job.result, job.error = outcome
                job.finished = time.time()
                job.fn = lambda: {}  # drop references (e.g. uploaded image)

    def _prune(self):
        cutoff = time.time() - KEEP_FINISHED_SECONDS
        stale = [j for j, job in self._jobs.items() if job.finished and job.finished < cutoff]
        for job_id in stale:
            del self._jobs[job_id]


job_manager = JobManager()
