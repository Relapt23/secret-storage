import base64
from fastapi import APIRouter, Depends
from src.app.schemas import Secret
from src.db.db_adapter import DBAdapter, get_db_adapter
from src.redis.redis_adapter import RedisAdapter

router = APIRouter()


@router.post("/secret")
async def create_secret(
    secret: Secret,
    db_adapter: DBAdapter = Depends(get_db_adapter),
    redis_adapter: RedisAdapter = Depends(RedisAdapter),
):
    encoded_secret = base64.b64encode(secret.secret.encode("utf-8")).decode("utf-8")
    secret_key = await db_adapter.create(
        encoded_secret, secret.passphrase, secret.ttl_seconds
    )
    return {"secret_key": secret_key}
