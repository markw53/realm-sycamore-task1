"""Job model definitions."""
import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 5
    LOW = 8
    BACKGROUND = 10


@dataclass
class Job:
    name: str
    payload: dict[str, Any]
    priority: int = JobPriority.MEDIUM.value
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 30.0
    tags: list[str] = field(default_factory=list)

    def start(self) -> None:
        if self.status not in (JobStatus.PENDING, JobStatus.RETRYING):
            raise InvalidJobStateError(
                f"Cannot start job in state {self.status.value}"
            )
        self.status = JobStatus.RUNNING
        self.started_at = time.time()

    def complete(self, result: Any = None) -> None:
        if self.status != JobStatus.RUNNING:
            raise InvalidJobStateError(
                f"Cannot complete job in state {self.status.value}"
            )
        self.status = JobStatus.COMPLETED
        self.result = result
        self.completed_at = time.time()

    def fail(self, error: str) -> None:
        if self.status != JobStatus.RUNNING:
            raise InvalidJobStateError(
                f"Cannot fail job in state {self.status.value}"
            )
        self.error = error
        if self.retry_count < self.max_retries:
            self.status = JobStatus.RETRYING
            self.retry_count += 1
        else:
            self.status = JobStatus.FAILED
            self.completed_at = time.time()

    def cancel(self) -> None:
        if self.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            raise InvalidJobStateError(
                f"Cannot cancel job in state {self.status.value}"
            )
        self.status = JobStatus.CANCELLED
        self.completed_at = time.time()

    @property
    def duration(self) -> Optional[float]:
        if self.started_at is None:
            return None
        end = self.completed_at or time.time()
        return end - self.started_at

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        data = data.copy()
        data["status"] = JobStatus(data["status"])
        return cls(**data)


class InvalidJobStateError(Exception):
    """Raised when a job state transition is invalid."""
    pass