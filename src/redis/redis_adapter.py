from fastapi import Depends

from src.redis.redis_config import make_redis
from redis.asyncio import Redis
from typing import Optional
import json
from src.app.schemas import CacheSecret


class RedisAdapter:
    def __init__(self, client: Redis):
        self.client = client

    async def update(self, secret_key: str, secret: str, ttl: Optional[int] = None):
        await self.client.set(
            name=secret_key,
            value=json.dumps({"secret": secret, "ttl": ttl}),
            ex=60 * 10,
        )

    async def get(self, secret_key: str) -> Optional[CacheSecret]:
        cache = await self.client.get(secret_key)
        if cache is None:
            return None
        secret_in_cache = json.loads(cache)
        return CacheSecret(
            secret=secret_in_cache.get("secret"), ttl=secret_in_cache.get("ttl")
        )

    def delete(self, secret_key: str) -> bool:
        pass


def make_redis_adapter(redis_client: Redis = Depends(make_redis)) -> RedisAdapter:
    return RedisAdapter(redis_client)
