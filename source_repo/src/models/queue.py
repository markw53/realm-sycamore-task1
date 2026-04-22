"""Thread-safe task queue implementation."""
import threading
import heapq
from typing import Optional
from src.models.job import Job


class TaskQueue:
    def __init__(self, max_size: int = 1000):
        self._max_size = max_size
        self._heap: list[tuple[int, float, Job]] = []
        self._lock = threading.Lock()
        self._counter = 0
        self._job_index: dict[str, Job] = {}

    def push(self, job: Job) -> None:
        with self._lock:
            if len(self._heap) >= self._max_size:
                raise QueueFullError(
                    f"Queue is full (max size: {self._max_size})"
                )
            if job.id in self._job_index:
                raise DuplicateJobError(f"Job {job.id} already in queue")
            entry = (job.priority, self._counter, job)
            self._counter += 1
            heapq.heappush(self._heap, entry)
            self._job_index[job.id] = job

    def pop(self) -> Optional[Job]:
        with self._lock:
            while self._heap:
                priority, counter, job = heapq.heappop(self._heap)
                if job.id in self._job_index:
                    del self._job_index[job.id]
                    return job
            return None

    def peek(self) -> Optional[Job]:
        with self._lock:
            for priority, counter, job in self._heap:
                if job.id in self._job_index:
                    return job
            return None

    def remove(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._job_index:
                del self._job_index[job_id]
                return True
            return False

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._job_index.get(job_id)

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._job_index)

    @property
    def is_empty(self) -> bool:
        return self.size == 0

    @property
    def is_full(self) -> bool:
        return self.size >= self._max_size

    def get_all_jobs(self) -> list[Job]:
        with self._lock:
            return list(self._job_index.values())

    def clear(self) -> int:
        with self._lock:
            count = len(self._job_index)
            self._heap.clear()
            self._job_index.clear()
            self._counter = 0
            return count


class QueueFullError(Exception):
    pass


class DuplicateJobError(Exception):
    pass