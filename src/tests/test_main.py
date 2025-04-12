import pytest
import base64
from unittest.mock import AsyncMock, MagicMock
from src.db.db_adapter import DBAdapter
from src.redis.redis_adapter import RedisAdapter
from src.app.schemas import Secret, SecretKeyInfo
from src.app.endpoints import create_secret


@pytest.mark.asyncio
async def test_create_secret_v2():
    # given
    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.create = AsyncMock(return_value="test_key")

    mock_redis_adapter = MagicMock(spec=RedisAdapter)

    # when
    res = await create_secret(
        secret=Secret(secret="Meow", passphrase=None, ttl_seconds=300),
        db_adapter=mock_db_adapter,
        redis_adapter=mock_redis_adapter,
    )

    # then
    assert res == SecretKeyInfo(secret_key="test_key")
    mock_db_adapter.create.assert_called_once_with(
        base64.b64encode(b"Meow").decode(), None, 300
    )
    mock_redis_adapter.update.assert_called_once_with(
        "test_key",
        base64.b64encode(b"Meow").decode(),
        300,
    )
