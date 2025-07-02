# Caching Example

This example demonstrates the built-in context cache with three resources:

- `slow_square` – request-scoped caching
- `fibonacci` – global caching across requests
- `user_analytics` – user-scoped caching

Run the example and observe the log output to see cache hits and misses.

```bash
cd caching
python app.py
```
