"""Worker for I/O-bound tasks."""
import asyncio
from typing import Any
from src.models.job import Job
from src.workers.base import BaseWorker


class IoWorker(BaseWorker):
    async def execute(self, job: Job) -> Any:
        action = job.payload.get("action")
        if action == "echo":
            delay = job.payload.get("delay", 0.1)
            message = job.payload.get("message", "")
            await asyncio.sleep(delay)
            return {"echoed": message}
        elif action == "transform":
            data = job.payload.get("data", {})
            operation = job.payload.get("operation", "identity")
            return self._transform(data, operation)
        elif action == "aggregate":
            items = job.payload.get("items", [])
            return self._aggregate(items)
        else:
            raise ValueError(f"Unknown IO action: {action}")

    @staticmethod
    def _transform(data: dict, operation: str) -> dict:
        if operation == "uppercase":
            return {k: v.upper() if isinstance(v, str) else v for k, v in data.items()}
        elif operation == "lowercase":
            return {k: v.lower() if isinstance(v, str) else v for k, v in data.items()}
        elif operation == "identity":
            return data.copy()
        elif operation == "keys_only":
            return {"keys": list(data.keys())}
        else:
            raise ValueError(f"Unknown transform operation: {operation}")

    @staticmethod
    def _aggregate(items: list) -> dict:
        if not items:
            return {"count": 0, "sum": 0, "avg": 0.0, "min": None, "max": None}
        numeric = [x for x in items if isinstance(x, (int, float))]
        if not numeric:
            return {"count": len(items), "sum": 0, "avg": 0.0, "min": None, "max": None}
        return {
            "count": len(numeric),
            "sum": sum(numeric),
            "avg": sum(numeric) / len(numeric),
            "min": min(numeric),
            "max": max(numeric),
        }