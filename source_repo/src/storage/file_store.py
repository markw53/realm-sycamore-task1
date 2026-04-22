"""File-based storage backend."""
import json
import os
from typing import Optional, Any
import aiofiles
from src.storage.backend import StorageBackend


class FileStorage(StorageBackend):
    def __init__(self, base_path: str = "./task_store"):
        self._base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _key_to_path(self, key: str) -> str:
        safe_key = key.replace("/", "_").replace("\\", "_")
        return os.path.join(self._base_path, f"{safe_key}.json")

    async def save(self, key: str, data: dict[str, Any]) -> None:
        path = self._key_to_path(key)
        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(data, default=str))

    async def load(self, key: str) -> Optional[dict[str, Any]]:
        path = self._key_to_path(key)
        if not os.path.exists(path):
            return None
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
            return json.loads(content)

    async def delete(self, key: str) -> bool:
        path = self._key_to_path(key)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    async def exists(self, key: str) -> bool:
        return os.path.exists(self._key_to_path(key))

    async def list_keys(self, prefix: str = "") -> list[str]:
        keys = []
        for fname in sorted(os.listdir(self._base_path)):
            if fname.endswith(".json"):
                key = fname[:-5]
                if key.startswith(prefix):
                    keys.append(key)
        return keys