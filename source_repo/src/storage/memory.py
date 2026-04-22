"""In-memory storage backend."""
from typing import Optional, Any
from src.storage.backend import StorageBackend


class MemoryStorage(StorageBackend):
    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def save(self, key: str, data: dict[str, Any]) -> None:
        self._store[key] = data.copy()

    async def load(self, key: str) -> Optional[dict[str, Any]]:
        val = self._store.get(key)
        return val.copy() if val else None

    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        return key in self._store

    async def list_keys(self, prefix: str = "") -> list[str]:
        return sorted(k for k in self._store if k.startswith(prefix))