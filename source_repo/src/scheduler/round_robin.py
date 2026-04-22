"""Round-robin scheduling strategy."""
from typing import Optional
from src.models.job import Job
from src.models.queue import TaskQueue


class RoundRobinScheduler:
    def __init__(self):
        self._name = "round_robin"
        self._last_tag_index: dict[str, int] = {}

    @property
    def name(self) -> str:
        return self._name

    def next_job(self, queue: TaskQueue) -> Optional[Job]:
        return queue.pop()

    def should_preempt(self, current: Job, incoming: Job) -> bool:
        return False