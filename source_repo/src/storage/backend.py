"""Abstract storage backend interface."""
from abc import ABC, abstractmethod
from typing import Optional, Any


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, key: str, data: dict[str, Any]) -> None: ...

    @abstractmethod
    async def load(self, key: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    async def delete(self, key: str) -> bool: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> list[str]: ...