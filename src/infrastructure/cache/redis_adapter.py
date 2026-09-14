"""Redis Cache Adapter for FAI scores and Open Payments wallet resolution cache."""
import json
from typing import Any
from uuid import UUID


class RedisCacheAdapter:
    """Redis cache adapter providing async get/set/delete operations.

    Implements an in-memory fallback store when Redis is unavailable,
    enabling the full application to run without a Redis instance.
    """

    def __init__(self, redis_client: Any = None) -> None:
        """Initialises the cache adapter.

        Args:
            redis_client: An aioredis or redis-py async client. If None,
                          an in-memory dictionary is used as fallback.
        """
        self._redis = redis_client
        self._memory_store: dict[str, str] = {}
        self._use_memory = redis_client is None

    async def get(self, key: str) -> Any | None:
        """Retrieves a value from cache by key.

        Args:
            key: Cache key string.

        Returns:
            Deserialized Python object, or None if cache miss.
        """
        if self._use_memory:
            raw = self._memory_store.get(key)
        else:
            raw = await self._redis.get(key)

        if raw is None:
            return None

        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 300,
    ) -> None:
        """Stores a serialized value in cache.

        Args:
            key: Cache key string.
            value: Serializable Python object.
            ttl_seconds: Time-to-live in seconds (default: 5 minutes).
        """
        serialized = json.dumps(value, default=str)

        if self._use_memory:
            self._memory_store[key] = serialized
        else:
            await self._redis.set(key, serialized, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        """Removes a key from cache.

        Args:
            key: Cache key to remove.
        """
        if self._use_memory:
            self._memory_store.pop(key, None)
        else:
            await self._redis.delete(key)

    async def invalidate_profile(self, profile_id: UUID) -> None:
        """Invalidates all cached data related to a given profile ID.

        Args:
            profile_id: The UUID of the profile to invalidate.
        """
        prefix = f"fai:profile:{profile_id}"
        if self._use_memory:
            keys_to_delete = [k for k in self._memory_store if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._memory_store[key]
        else:
            # In production: use SCAN + DEL pipeline for efficiency
            async for key in self._redis.scan_iter(f"{prefix}:*"):
                await self._redis.delete(key)

    @staticmethod
    def score_key(profile_id: UUID) -> str:
        """Generates a standardized cache key for a profile's latest FAI score."""
        return f"fai:profile:{profile_id}:latest_score"

    @staticmethod
    def wallet_key(wallet_url: str) -> str:
        """Generates a standardized cache key for a resolved wallet address."""
        return f"fai:wallet:{wallet_url}"
