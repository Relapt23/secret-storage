import base64
from fastapi import APIRouter, Depends, HTTPException
from src.app.schemas import Secret, SecretInfo, SecretKeyInfo, DeletedSecret
from src.db.db_adapter import DBAdapter, make_db_adapter
from src.redis.redis_adapter import RedisAdapter, make_redis_adapter

router = APIRouter()


@router.post("/secret")
async def create_secret(
    secret: Secret,
    db_adapter: DBAdapter = Depends(make_db_adapter),
    redis_adapter: RedisAdapter = Depends(make_redis_adapter),
) -> SecretKeyInfo:
    encoded_secret = base64.b64encode(secret.secret.encode("utf-8")).decode("utf-8")

    secret_key = await db_adapter.create(
        encoded_secret, secret.passphrase, secret.ttl_seconds
    )
    await redis_adapter.update(secret_key, encoded_secret, secret.ttl_seconds)

    return SecretKeyInfo(secret_key=secret_key)


@router.get("/secret/{secret_key}")
async def get_secret(
    secret_key: str,
    db_adapter: DBAdapter = Depends(make_db_adapter),
    redis_adapter: RedisAdapter = Depends(make_redis_adapter),
) -> SecretInfo:
    secret_in_cache = await redis_adapter.get(secret_key)

    if secret_in_cache:
        decoded_secret = base64.b64decode(
            secret_in_cache.secret.encode("utf-8")
        ).decode("utf-8")

        await redis_adapter.delete(secret_key)
        await db_adapter.delete(secret_key)

        return SecretInfo(secret=decoded_secret)

    secret_in_db = await db_adapter.get(secret_key)
    if secret_in_db:
        decoded_secret = base64.b64decode(secret_in_db.secret.encode("utf-8")).decode("utf-8")
        await db_adapter.delete(secret_key)

        return SecretInfo(secret=decoded_secret)

    raise HTTPException(detail="secret_not_found", status_code=404)


@router.delete("/secret/{secret_key}")
async def delete_secret(
    secret_key: str,
    db_adapter: DBAdapter = Depends(make_db_adapter),
    redis_adapter: RedisAdapter = Depends(make_redis_adapter),
) -> DeletedSecret:
    deleted_cache_secret = await redis_adapter.delete(secret_key)
    deleted_db_secret = await db_adapter.delete(secret_key)

    if deleted_cache_secret or deleted_db_secret:
        return DeletedSecret(status="secret_deleted")

    raise HTTPException(status_code=404, detail="secret_not_deleted")
