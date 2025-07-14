"""Caching utilities for EnrichMCP."""

from __future__ import annotations

import asyncio
import hashlib
import pickle
import re
import time
import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:  # pragma: no cover - used for type hints
    from collections.abc import Callable

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None  # type: ignore


class CacheBackend(ABC):
    """Abstract cache backend interface."""

    @abstractmethod
    async def get(self, namespace: str, key: str) -> Any | None:
        """Retrieve a cached value or ``None`` if it does not exist."""
        pass

    @abstractmethod
    async def set(self, namespace: str, key: str, value: Any, ttl: int | None = None) -> None:
        """Store ``value`` in ``namespace`` with optional ``ttl`` in seconds."""
        pass

    @abstractmethod
    async def delete(self, namespace: str, key: str) -> bool:
        """Remove ``key`` from ``namespace``. Returns ``True`` if deleted."""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache backend."""

    def __init__(self) -> None:
        """Initialize the in-memory store and a lock for concurrency."""
        self._data: dict[str, dict[str, tuple[Any, float | None]]] = {}
        self._lock = asyncio.Lock()

    async def get(self, namespace: str, key: str) -> Any | None:
        """Return a cached value if present and not expired."""
        async with self._lock:
            ns = self._data.get(namespace)
            if not ns or key not in ns:
                return None
            value, expires = ns[key]
            if expires is not None and expires < time.monotonic():
                ns.pop(key, None)
                if not ns:
                    self._data.pop(namespace, None)
                return None
            return value

    async def set(self, namespace: str, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value with an optional expiry time."""
        async with self._lock:
            expires = time.monotonic() + ttl if ttl else None
            self._data.setdefault(namespace, {})[key] = (value, expires)

    async def delete(self, namespace: str, key: str) -> bool:
        """Remove a key from the cache."""
        async with self._lock:
            ns = self._data.get(namespace)
            if not ns or key not in ns:
                return False
            ns.pop(key, None)
            if not ns:
                self._data.pop(namespace, None)
            return True


class RedisCache(CacheBackend):
    """Redis-based cache backend."""

    def __init__(self, url: str, redis_client: Any | None = None) -> None:
        """Initialize the cache.

        Parameters
        ----------
        url:
            Redis connection URL. Ignored if ``redis_client`` is provided.
        redis_client:
            Optional pre-configured redis client. Allows injecting a fake
            instance such as ``fakeredis`` for tests without monkeypatching.
        """

        if redis_client is not None:
            self._redis = redis_client
            return
        if redis is None:  # pragma: no cover - optional dependency
            raise ImportError("redis package is required for RedisCache")
        self._redis = redis.from_url(url)

    async def get(self, namespace: str, key: str) -> Any | None:
        """Return the cached value stored under ``namespace`` and ``key``."""
        raw = await self._redis.get(f"{namespace}:{key}")
        return pickle.loads(raw) if raw is not None else None

    async def set(self, namespace: str, key: str, value: Any, ttl: int | None = None) -> None:
        """Store ``value`` in Redis with an optional TTL."""
        await self._redis.set(f"{namespace}:{key}", pickle.dumps(value), ex=ttl)

    async def delete(self, namespace: str, key: str) -> bool:
        """Delete a key from Redis and return ``True`` if removed."""
        return await self._redis.delete(f"{namespace}:{key}") > 0


DEFAULT_TTLS = {"global": 3600, "user": 1800, "request": 300}


class ContextCache:
    """Cache manager bound to a request context."""

    def __init__(self, backend: CacheBackend, cache_id: str, request_id: str) -> None:
        """Create a context-specific cache namespace."""
        self._backend = backend
        self._cache_id = cache_id
        cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", str(request_id))
        self._request_id = cleaned if cleaned else uuid4().hex

    def _user_hash(self) -> str | None:
        """Return a short hash derived from the current access token."""
        try:
            from mcp.server.auth.middleware.auth_context import get_access_token  # type: ignore
        except Exception:  # pragma: no cover - optional dependency
            return None
        token = get_access_token()
        if token is None:
            return None
        return hashlib.sha256(token.token.encode()).hexdigest()[:16]

    def _build_namespace(self, scope: str) -> str:
        """Return a fully-qualified cache namespace for the given scope."""
        if scope == "global":
            return f"enrichmcp:global:{self._cache_id}"
        if scope == "user":
            user = self._user_hash()
            if user is None:
                warnings.warn(
                    "User cache requested but no access token found; falling back to request scope",
                    stacklevel=2,
                )
                return self._build_namespace("request")
            return f"enrichmcp:user:{self._cache_id}:{user}"
        if scope == "request":
            return f"enrichmcp:request:{self._cache_id}:{self._request_id}"
        raise ValueError(f"Unknown cache scope: {scope}")

    def _ttl(self, scope: str, ttl: int | None) -> int | None:
        """Resolve ``ttl`` using defaults for the specified scope."""
        return ttl if ttl is not None else DEFAULT_TTLS.get(scope)

    async def get(self, key: str, scope: str = "request") -> Any | None:
        """Retrieve a cached value for ``key`` within ``scope``."""
        return await self._backend.get(self._build_namespace(scope), key)

    async def set(
        self, key: str, value: Any, scope: str = "request", ttl: int | None = None
    ) -> None:
        """Store ``value`` under ``key`` with an optional ``ttl``."""
        await self._backend.set(self._build_namespace(scope), key, value, self._ttl(scope, ttl))

    async def delete(self, key: str, scope: str = "request") -> bool:
        """Remove ``key`` from the specified ``scope``."""
        return await self._backend.delete(self._build_namespace(scope), key)

    async def get_or_set(
        self, key: str, factory: Callable[[], Any], scope: str = "request", ttl: int | None = None
    ) -> Any:
        """Return cached ``key`` or compute and store it using ``factory``."""
        cached = await self.get(key, scope)
        if cached is not None:
            return cached
        value = await factory()
        await self.set(key, value, scope, ttl)
        return value
