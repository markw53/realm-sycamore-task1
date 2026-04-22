"""Configuration management for the task queue."""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class QueueConfig:
    max_workers: int = 4
    max_queue_size: int = 1000
    default_priority: int = 5
    scheduling_strategy: Literal["priority", "round_robin"] = "priority"
    storage_backend: Literal["memory", "file"] = "memory"
    storage_path: str = "./task_store"
    retry_limit: int = 3
    timeout_seconds: float = 30.0
    log_level: str = "INFO"

    def __post_init__(self):
        if self.max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if self.max_queue_size < 1:
            raise ValueError("max_queue_size must be >= 1")
        if self.default_priority < 0 or self.default_priority > 10:
            raise ValueError("default_priority must be between 0 and 10")
        if self.retry_limit < 0:
            raise ValueError("retry_limit must be >= 0")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")