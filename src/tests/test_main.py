import pytest
import base64
from unittest.mock import AsyncMock, MagicMock, Mock
from src.db.db_adapter import DBAdapter
from src.redis.redis_adapter import RedisAdapter
from src.app.schemas import Secret, SecretKeyInfo, CacheSecret, SecretInfo
from src.app.endpoints import create_secret, get_secret


@pytest.mark.asyncio
async def test_create_secret():
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


@pytest.mark.asyncio
async def test_get_secret_in_cache():
    # given
    encoded = base64.b64encode(b"Meow").decode("utf-8")
    mock_db_adapter = MagicMock(spec=DBAdapter)

    mock_redis_adapter = MagicMock(spec=RedisAdapter)
    mock_redis_adapter.get = AsyncMock(
        return_value=CacheSecret(secret=encoded, ttl=None)
    )

    # when
    res = await get_secret(
        secret_key="test_key",
        db_adapter=mock_db_adapter,
        redis_adapter=mock_redis_adapter,
    )

    # then
    assert res == SecretInfo(secret="Meow")
    mock_redis_adapter.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_get_secret_in_db():
    # given
    encoded = base64.b64encode(b"Meow").decode("utf-8")
    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.get = AsyncMock(return_value=Mock(secret=encoded))

    mock_redis_adapter = MagicMock(spec=RedisAdapter)
    mock_redis_adapter.get = AsyncMock(return_value=None)

    # when
    res = await get_secret(
        secret_key="test_key",
        db_adapter=mock_db_adapter,
        redis_adapter=mock_redis_adapter,
    )

    # then
    assert res == SecretInfo(secret="Meow")
    mock_db_adapter.get.assert_called_once_with("test_key")
