import base64
from fastapi import APIRouter, Depends
from src.app.schemas import Secret, CustomException
from src.db.db_adapter import DBAdapter, make_db_adapter
from src.redis.redis_adapter import RedisAdapter, make_redis_adapter

router = APIRouter()


@router.post("/secret")
async def create_secret(
    secret: Secret,
    db_adapter: DBAdapter = Depends(make_db_adapter),
    redis_adapter: RedisAdapter = Depends(make_redis_adapter),
):
    encoded_secret = base64.b64encode(secret.secret.encode("utf-8")).decode("utf-8")
    secret_key = await db_adapter.create(
        encoded_secret, secret.passphrase, secret.ttl_seconds
    )
    await redis_adapter.update(secret_key, encoded_secret, secret.ttl_seconds)
    return {"secret_key": secret_key}


@router.get("/secret/{secret_key}")
async def get_secret(
    secret_key: str,
    db_adapter: DBAdapter = Depends(make_db_adapter),
    redis_adapter: RedisAdapter = Depends(make_redis_adapter),
):
    secret_in_cache = await redis_adapter.get(secret_key)
    if secret_in_cache:
        await redis_adapter.delete(secret_key)
        await db_adapter.delete(secret_key)
        return {"secret": secret_in_cache.secret}

    secret_in_db = await db_adapter.get(secret_key)
    if secret_in_db:
        await db_adapter.delete(secret_key)
        return {"secret": secret_in_db}
    else:
        raise CustomException(detail="secret_not_found", status_code=404)
