from fastapi import Depends

from src.redis.redis_config import get_redis
from redis.asyncio import Redis
from typing import Optional
import json


class RedisAdapter:
    def __init__(self, client: Redis):
        self.client = client

    async def update(self, secret_key: str, secret: str, ttl: Optional[int] = None):
        await self.client.set(
            name=secret_key,
            value=json.dumps({"secret": secret, "ttl": ttl}),
            ex=60 * 10,
        )

    async def get(self, secret_key: str) -> str | None:
        cache = await self.client.get(secret_key)
        secret_in_cache = await json.loads(cache)
        return secret_in_cache

    def delete(self, secret_key: str) -> bool:
        pass


def get_redis_adapter(redis_client: Redis = Depends(get_redis)) -> RedisAdapter:
    return RedisAdapter(redis_client)
