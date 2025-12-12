"""Redis test configuration and fixtures."""

import os
import shutil
import subprocess
import time

import pytest
import pytest_asyncio

# Only import redis if available
redis_async = pytest.importorskip("redis.asyncio", reason="Redis package not available")


def docker_available() -> bool:
    """Check if Docker is available."""
    return shutil.which("docker") is not None


def redis_running_on_port(port: int = 6379) -> bool:
    """Check if Redis is already running on the specified port."""
    try:
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", port))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture(scope="session")
def redis_container():
    """Manage Redis container lifecycle for tests.

    This fixture:
    1. Checks if Redis is already running (for CI or manual setup)
    2. If not, tries to start a Docker container
    3. Skips tests gracefully if neither is available
    """
    # Check if Redis is already running (CI environment or manual setup)
    if redis_running_on_port(6379):
        yield {"host": "localhost", "port": 6379}
        return

    # Check if we're in CI and should use a service
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        # In CI, Redis should be provided as a service
        # If not available, skip tests
        pytest.skip("Redis service not available in CI environment")

    # Local development - try to start Docker container
    if not docker_available():
        pytest.skip("Docker not available and Redis not running - skipping Redis tests")

    # Determine docker compose command
    if shutil.which("docker-compose"):
        compose_cmd = ["docker-compose", "-f", "docker-compose.test.yml"]
    else:
        compose_cmd = ["docker", "compose", "-f", "docker-compose.test.yml"]

    # Start Redis container
    try:
        subprocess.run(
            [*compose_cmd, "up", "-d", "--wait"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout
        )

        # Give Redis a moment to be fully ready
        time.sleep(2)

        # Verify Redis is actually responding
        if not redis_running_on_port(6379):
            raise RuntimeError("Redis container started but not responding")

        yield {"host": "localhost", "port": 6379}

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, RuntimeError) as e:
        pytest.skip(f"Failed to start Redis container: {e}")
    finally:
        # Cleanup: stop and remove containers (best effort)
        import contextlib

        with contextlib.suppress(Exception):
            subprocess.run(
                [*compose_cmd, "down", "-v"],
                check=False,  # Don't fail if cleanup fails
                capture_output=True,
                text=True,
                timeout=30,
            )


@pytest_asyncio.fixture(scope="function")
async def redis_client(redis_container):
    """Provide a clean Redis client for each test."""
    client = redis_async.Redis(
        host=redis_container["host"], port=redis_container["port"], decode_responses=False
    )

    try:
        # Ensure Redis is ready and flush any existing data
        await client.ping()
        await client.flushall()
        yield client
    finally:
        await client.aclose()
