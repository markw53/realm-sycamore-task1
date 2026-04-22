"""Priority-based scheduling strategy."""
from typing import Optional
from src.models.job import Job
from src.models.queue import TaskQueue


class PriorityScheduler:
    def __init__(self):
        self._name = "priority"

    @property
    def name(self) -> str:
        return self._name

    def next_job(self, queue: TaskQueue) -> Optional[Job]:
        return queue.pop()

    def should_preempt(self, current: Job, incoming: Job) -> bool:
        return incoming.priority < current.priority