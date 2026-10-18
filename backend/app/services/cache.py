"""轻量进程内缓存（替代 Redis 的单机方案）：

- 支持 TTL 与容量上限
- 检索结果缓存：知识库版本号变化时自动失效（入库/删除后版本 +1）
"""
import hashlib
import threading
import time
from collections import OrderedDict

from app.core.config import get_settings

_kb_version = 0
_version_lock = threading.Lock()


def bump_kb_version() -> None:
    """知识库发生变更（入库/删除）时调用，令检索缓存整体失效。"""
    global _kb_version
    with _version_lock:
        _kb_version += 1


def kb_version() -> int:
    return _kb_version


class TTLCache:
    """线程安全的有界 TTL 缓存（LRU 淘汰）。"""

    def __init__(self, maxsize: int = 128, ttl: float = 300):
        self._maxsize = maxsize
        self._ttl = ttl
        self._store: OrderedDict[str, tuple[float, object]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expire_at, value = item
            if time.time() > expire_at:
                self._store.pop(key, None)
                return None
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value) -> None:
        with self._lock:
            self._store[key] = (time.time() + self._ttl, value)
            self._store.move_to_end(key)
            while len(self._store) > self._maxsize:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


def retrieval_cache_key(query: str, top_k: int) -> str:
    payload = f"{query}|{top_k}|v{kb_version()}"
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


_retrieval_cache: TTLCache | None = None


def get_retrieval_cache() -> TTLCache:
    global _retrieval_cache
    if _retrieval_cache is None:
        settings = get_settings()
        _retrieval_cache = TTLCache(maxsize=settings.RETRIEVAL_CACHE_MAXSIZE, ttl=settings.RETRIEVAL_CACHE_TTL)
    return _retrieval_cache


def clear_retrieval_cache() -> None:
    if _retrieval_cache is not None:
        _retrieval_cache.clear()
