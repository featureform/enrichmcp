import asyncio

import pytest

from enrichmcp.cache import ContextCache, MemoryCache


@pytest.mark.asyncio
async def test_memory_cache_ttl_and_delete():
    backend = MemoryCache()
    await backend.set("ns", "key", "value", ttl=1)
    assert await backend.get("ns", "key") == "value"
    await asyncio.sleep(1.1)
    assert await backend.get("ns", "key") is None
    await backend.set("ns", "key", "value")
    assert await backend.delete("ns", "key") is True
    assert await backend.get("ns", "key") is None


@pytest.mark.asyncio
async def test_context_cache_get_or_set():
    backend = MemoryCache()
    cache = ContextCache(backend, "app", "req1")

    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        return "data"

    v1 = await cache.get_or_set("k", factory)
    v2 = await cache.get_or_set("k", factory)
    assert v1 == "data" and v2 == "data"
    assert calls == 1


@pytest.mark.asyncio
async def test_user_scope_warns_and_falls_back(monkeypatch):
    backend = MemoryCache()
    cache = ContextCache(backend, "app", "req")

    monkeypatch.setattr(cache, "_user_hash", lambda: None)
    with pytest.warns(UserWarning):
        ns = cache._build_namespace("user")

    assert ns == cache._build_namespace("request")


@pytest.mark.asyncio
async def test_request_id_sanitization_and_unique_fallback():
    backend = MemoryCache()
    cache = ContextCache(backend, "app", "bad:id")
    assert cache._build_namespace("request") == "enrichmcp:request:app:bad_id"

    c1 = ContextCache(backend, "app", "")
    c2 = ContextCache(backend, "app", "")
    assert c1._request_id != c2._request_id
