# Cache

EnrichMCP includes a simple caching system available from `EnrichContext.cache`.
It stores values in namespaces scoped to the current **request**, **authenticated user**, or **application**.
The cache uses pluggable backends so you can keep data in memory or an external store like Redis.

## ContextCache

The `ContextCache` class is created for every request. Use its helper methods to
store or retrieve data:

```python
value = await ctx.cache.get_or_set("key", factory, scope="request", ttl=None)
await ctx.cache.set("key", value, scope="user")
cached = await ctx.cache.get("key", scope="global")
await ctx.cache.delete("key")
```

Cache namespaces are generated automatically using your app's ID, the request ID
and, for user scope, a hash of the access token:

```
enrichmcp:global:{app_id}
enrichmcp:user:{app_id}:{user_hash}
enrichmcp:request:{app_id}:{request_id}
```

Default TTLs are `global=3600`, `user=1800`, and `request=300` seconds. If the
user scope is requested but no access token is available a warning is emitted
and the key is stored in the request scope instead.

## Backends

Two backends are provided:

- `MemoryCache` – in-memory storage used by default
- `RedisCache` – persistent storage backed by Redis

::: enrichmcp.cache.ContextCache
    options:
        show_source: true

::: enrichmcp.cache.MemoryCache

::: enrichmcp.cache.RedisCache
