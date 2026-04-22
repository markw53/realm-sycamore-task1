"""Entry point for the task queue system."""
import asyncio
from src.config import QueueConfig
from src.models.job import Job, JobPriority
from src.scheduler.scheduler import Scheduler
from src.utils.logging import configure_logging
import structlog

logger = structlog.get_logger()


async def main():
    configure_logging("INFO")

    config = QueueConfig(
        max_workers=4,
        max_queue_size=100,
        scheduling_strategy="priority",
        storage_backend="memory",
    )

    scheduler = Scheduler(config)

    jobs = [
        Job(name="factorial-job", payload={"action": "factorial", "n": 20}, priority=JobPriority.HIGH.value),
        Job(name="echo-job", payload={"action": "echo", "message": "hello", "delay": 0.1}, priority=JobPriority.LOW.value),
        Job(name="fibonacci-job", payload={"action": "fibonacci", "n": 30}, priority=JobPriority.MEDIUM.value),
        Job(name="prime-check", payload={"action": "prime_check", "n": 97}, priority=JobPriority.CRITICAL.value),
        Job(name="transform-job", payload={"action": "transform", "data": {"name": "test"}, "operation": "uppercase"}, priority=JobPriority.MEDIUM.value),
        Job(name="aggregate-job", payload={"action": "aggregate", "items": [1, 2, 3, 4, 5]}, priority=JobPriority.BACKGROUND.value),
    ]

    for job in jobs:
        scheduler.submit(job)

    logger.info("starting_scheduler", queue_size=scheduler.queue.size)
    results = await scheduler.run_all()

    for result in results:
        status = "✓" if result.success else "✗"
        logger.info("result", status=status, job_id=result.job_id[:8], value=result.value, error=result.error)

    stats = scheduler.get_stats()
    logger.info("final_stats", **stats)


if __name__ == "__main__":
    asyncio.run(main())