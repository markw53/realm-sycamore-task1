"""Main scheduler orchestrator."""
import asyncio
from typing import Optional, Any
from src.config import QueueConfig
from src.models.job import Job, JobStatus
from src.models.queue import TaskQueue
from src.models.result import JobResult
from src.scheduler.priority import PriorityScheduler
from src.scheduler.round_robin import RoundRobinScheduler
from src.workers.base import BaseWorker
from src.workers.cpu_worker import CpuWorker
from src.workers.io_worker import IoWorker
import structlog

logger = structlog.get_logger()

# Maps actions to the worker class that can handle them
CPU_ACTIONS = {"factorial", "fibonacci", "prime_check"}
IO_ACTIONS = {"echo", "transform", "aggregate"}


class Scheduler:
    def __init__(self, config: QueueConfig):
        self.config = config
        self.queue = TaskQueue(max_size=config.max_queue_size)
        self._results: dict[str, JobResult] = {}
        self._running = False

        if config.scheduling_strategy == "priority":
            self._strategy = PriorityScheduler()
        else:
            self._strategy = RoundRobinScheduler()

        self._workers: list[BaseWorker] = []
        for i in range(config.max_workers):
            if i % 2 == 0:
                self._workers.append(CpuWorker(f"cpu-{i}", config.timeout_seconds))
            else:
                self._workers.append(IoWorker(f"io-{i}", config.timeout_seconds))

    def submit(self, job: Job) -> str:
        if job.priority < 0 or job.priority > 10:
            raise ValueError(f"Priority must be 0-10, got {job.priority}")
        self.queue.push(job)
        logger.info("job_submitted", job_id=job.id, name=job.name, priority=job.priority)
        return job.id

    def _get_compatible_worker(self, job: Job) -> Optional[BaseWorker]:
        """Find an available worker that can handle this job's action type."""
        action = job.payload.get("action", "")

        if action in CPU_ACTIONS:
            target_type = CpuWorker
        elif action in IO_ACTIONS:
            target_type = IoWorker
        else:
            # Unknown action — try any available worker
            target_type = BaseWorker

        for worker in self._workers:
            if not worker.is_busy and isinstance(worker, target_type):
                return worker

        # Fallback: if no compatible worker is free, return None
        return None

    async def process_next(self) -> Optional[JobResult]:
        # Peek first to check if we have a compatible worker before popping
        peeked = self.queue.peek()
        if peeked is None:
            return None

        worker = self._get_compatible_worker(peeked)
        if worker is None:
            return None

        job = self._strategy.next_job(self.queue)
        if job is None:
            return None

        job.start()
        result = await worker.run(job)

        if result.success:
            job.complete(result.value)
        else:
            job.fail(result.error or "Unknown error")
            if job.status == JobStatus.RETRYING:
                logger.info("job_retrying", job_id=job.id, attempt=job.retry_count)
                self.queue.push(job)
                return result

        self._results[job.id] = result
        return result

    async def run_all(self) -> list[JobResult]:
        results = []
        self._running = True
        while not self.queue.is_empty and self._running:
            result = await self.process_next()
            if result:
                results.append(result)
            else:
                await asyncio.sleep(0.01)
        self._running = False
        return results

    def stop(self) -> None:
        self._running = False

    def get_result(self, job_id: str) -> Optional[JobResult]:
        return self._results.get(job_id)

    def get_all_results(self) -> list[JobResult]:
        return list(self._results.values())

    def get_stats(self) -> dict[str, Any]:
        return {
            "queue_size": self.queue.size,
            "total_results": len(self._results),
            "successful": sum(1 for r in self._results.values() if r.success),
            "failed": sum(1 for r in self._results.values() if not r.success),
            "strategy": self._strategy.name,
            "workers": [w.stats for w in self._workers],
        }