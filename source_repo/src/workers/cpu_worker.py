"""Worker for CPU-bound tasks simulated via asyncio."""
import asyncio
import math
from typing import Any
from src.models.job import Job
from src.workers.base import BaseWorker


class CpuWorker(BaseWorker):
    async def execute(self, job: Job) -> Any:
        action = job.payload.get("action")
        if action == "factorial":
            n = job.payload.get("n", 0)
            if not isinstance(n, int) or n < 0:
                raise ValueError(f"Invalid factorial input: {n}")
            result = await asyncio.to_thread(math.factorial, n)
            return {"factorial": result}
        elif action == "fibonacci":
            n = job.payload.get("n", 0)
            if not isinstance(n, int) or n < 0:
                raise ValueError(f"Invalid fibonacci input: {n}")
            result = await asyncio.to_thread(self._fibonacci, n)
            return {"fibonacci": result}
        elif action == "prime_check":
            n = job.payload.get("n", 0)
            if not isinstance(n, int) or n < 2:
                return {"is_prime": False}
            result = await asyncio.to_thread(self._is_prime, n)
            return {"is_prime": result}
        else:
            raise ValueError(f"Unknown CPU action: {action}")

    @staticmethod
    def _fibonacci(n: int) -> int:
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True