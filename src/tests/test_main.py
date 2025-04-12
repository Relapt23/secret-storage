import pytest
import base64
from unittest.mock import AsyncMock, MagicMock, Mock
from src.db.db_adapter import DBAdapter
from src.redis.redis_adapter import RedisAdapter
from src.app.schemas import (
    Secret,
    SecretKeyInfo,
    CacheSecret,
    SecretInfo,
    DeletedSecret,
)
from src.app.endpoints import create_secret, get_secret, delete_secret
from fastapi import HTTPException


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


@pytest.mark.asyncio
async def test_get_secret_not_found():
    # given
    mock_redis_adapter = MagicMock(spec=RedisAdapter)
    mock_redis_adapter.get = AsyncMock(return_value=None)

    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.get = AsyncMock(return_value=None)

    # when
    with pytest.raises(HTTPException) as exception:
        await get_secret(
            secret_key="test_key",
            db_adapter=mock_db_adapter,
            redis_adapter=mock_redis_adapter,
        )

    # then
    assert exception.value.status_code == 404
    assert exception.value.detail == "secret_not_found"
    mock_redis_adapter.get.assert_called_once_with("test_key")
    mock_db_adapter.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_delete_secret_in_cache():
    # given
    mock_redis_adapter = MagicMock(spec=RedisAdapter)
    mock_redis_adapter.delete = AsyncMock(return_value=True)

    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.delete = AsyncMock(return_value=None)

    # when
    res = await delete_secret(
        secret_key="test_key",
        db_adapter=mock_db_adapter,
        redis_adapter=mock_redis_adapter,
    )

    # then
    assert res == DeletedSecret(status="secret_deleted")
    mock_redis_adapter.delete.assert_called_once_with("test_key")
    mock_db_adapter.delete.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_delete_secret_in_db():
    # given
    mock_redis_adapter = MagicMock(spec=RedisAdapter)
    mock_redis_adapter.delete = AsyncMock(return_value=False)

    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.delete = AsyncMock(return_value=True)

    # when
    res = await delete_secret(
        secret_key="test_key",
        db_adapter=mock_db_adapter,
        redis_adapter=mock_redis_adapter,
    )

    # then
    assert res == DeletedSecret(status="secret_deleted")
    mock_redis_adapter.delete.assert_called_once_with("test_key")
    mock_db_adapter.delete.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_delete_secret_in_db_and_cache():
    # given
    mock_redis_adapter = MagicMock(spec=RedisAdapter)
    mock_redis_adapter.delete = AsyncMock(return_value=True)

    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.delete = AsyncMock(return_value=True)

    # when
    res = await delete_secret(
        secret_key="test_key",
        db_adapter=mock_db_adapter,
        redis_adapter=mock_redis_adapter,
    )

    # then
    assert res == DeletedSecret(status="secret_deleted")
    mock_redis_adapter.delete.assert_called_once_with("test_key")
    mock_db_adapter.delete.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_delete_secret_not_found():
    # given
    mock_redis_adapter = MagicMock(spec=RedisAdapter)
    mock_redis_adapter.delete = AsyncMock(return_value=False)

    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.delete = AsyncMock(return_value=False)

    # when
    with pytest.raises(HTTPException) as exception:
        await delete_secret(
            secret_key="test_key",
            db_adapter=mock_db_adapter,
            redis_adapter=mock_redis_adapter,
        )

    # then
    assert exception.value.status_code == 404
    assert exception.value.detail == "secret_not_deleted"
    mock_redis_adapter.delete.assert_called_once_with("test_key")
    mock_db_adapter.delete.assert_called_once_with("test_key")
