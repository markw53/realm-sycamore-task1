"""Result container for job execution outcomes."""
from dataclasses import dataclass, field
from typing import Any, Optional
import time


@dataclass
class JobResult:
    job_id: str
    success: bool
    value: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_error(self) -> bool:
        return not self.success

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "success": self.success,
            "value": self.value,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobResult":
        return cls(**data)

    @classmethod
    def ok(cls, job_id: str, value: Any = None, **metadata) -> "JobResult":
        return cls(job_id=job_id, success=True, value=value, metadata=metadata)

    @classmethod
    def err(cls, job_id: str, error: str, **metadata) -> "JobResult":
        return cls(job_id=job_id, success=False, error=error, metadata=metadata)