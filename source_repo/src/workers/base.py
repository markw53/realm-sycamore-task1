"""Base worker interface."""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any
from src.models.job import Job
from src.models.result import JobResult
import structlog

logger = structlog.get_logger()


class BaseWorker(ABC):
    def __init__(self, worker_id: str, timeout: float = 30.0):
        self.worker_id = worker_id
        self.timeout = timeout
        self._is_busy = False
        self._jobs_processed = 0
        self._total_execution_time = 0.0

    @abstractmethod
    async def execute(self, job: Job) -> Any:
        """Execute the job's payload. Must be implemented by subclasses."""
        ...

    async def run(self, job: Job) -> JobResult:
        self._is_busy = True
        start = time.time()
        try:
            result = await asyncio.wait_for(
                self.execute(job), timeout=job.timeout or self.timeout
            )
            elapsed = time.time() - start
            self._jobs_processed += 1
            self._total_execution_time += elapsed
            logger.info(
                "job_completed",
                worker=self.worker_id,
                job_id=job.id,
                elapsed=round(elapsed, 3),
            )
            return JobResult.ok(
                job_id=job.id, value=result, worker=self.worker_id
            )
        except asyncio.TimeoutError:
            elapsed = time.time() - start
            logger.warning(
                "job_timeout",
                worker=self.worker_id,
                job_id=job.id,
                timeout=job.timeout,
            )
            return JobResult.err(
                job_id=job.id,
                error=f"Timeout after {job.timeout}s",
                worker=self.worker_id,
            )
        except Exception as e:
            elapsed = time.time() - start
            logger.error(
                "job_failed",
                worker=self.worker_id,
                job_id=job.id,
                error=str(e),
            )
            return JobResult.err(
                job_id=job.id, error=str(e), worker=self.worker_id
            )
        finally:
            self._is_busy = False

    @property
    def is_busy(self) -> bool:
        return self._is_busy

    @property
    def stats(self) -> dict[str, Any]:
        avg = (
            self._total_execution_time / self._jobs_processed
            if self._jobs_processed > 0
            else 0.0
        )
        return {
            "worker_id": self.worker_id,
            "jobs_processed": self._jobs_processed,
            "total_execution_time": round(self._total_execution_time, 3),
            "average_execution_time": round(avg, 3),
            "is_busy": self._is_busy,
        }