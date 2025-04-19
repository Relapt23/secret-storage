import uuid

import pytest
import base64
from datetime import datetime, UTC
from freezegun import freeze_time
from unittest.mock import AsyncMock, MagicMock
from src.db.db_adapter import DBAdapter
from src.db.models import SecretBase
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


@pytest.fixture
def frozen_time():
    with freeze_time(datetime.fromtimestamp(1744870851, UTC)) as frozen:
        yield frozen


@pytest.mark.asyncio
async def test_create_secret(frozen_time):
    # given
    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.create = AsyncMock(return_value="test_key")

    mock_redis_adapter = MagicMock(spec=RedisAdapter)

    # when
    res = await create_secret(
        secret=Secret(secret="Meow", passphrase=None, ttl_seconds=3),
        db_adapter=mock_db_adapter,
        redis_adapter=mock_redis_adapter,
    )

    # then
    assert res == SecretKeyInfo(secret_key="test_key")
    mock_db_adapter.create.assert_called_once_with(
        base64.b64encode(b"Meow").decode(), None, 1744870854.0
    )
    mock_redis_adapter.update.assert_called_once_with(
        "test_key",
        base64.b64encode(b"Meow").decode(),
        None,
        1744870854.0,
    )


@pytest.mark.asyncio
async def test_get_secret_in_cache():
    # given
    encoded = base64.b64encode(b"Meow").decode("utf-8")
    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.delete = AsyncMock(return_value=True)

    mock_redis_adapter = MagicMock(spec=RedisAdapter)
    mock_redis_adapter.get = AsyncMock(
        return_value=CacheSecret(secret=encoded, passphrase=None, expiration_date=None)
    )
    mock_redis_adapter.delete = AsyncMock(return_value=True)
    # when
    res = await get_secret(
        secret_key="test_key",
        db_adapter=mock_db_adapter,
        redis_adapter=mock_redis_adapter,
    )

    # then
    assert res == SecretInfo(secret="Meow")
    mock_redis_adapter.get.assert_called_once_with("test_key")
    mock_redis_adapter.delete.assert_called_once_with("test_key")
    mock_db_adapter.delete.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_get_secret_in_db():
    # given
    key = uuid.uuid4()
    encoded = base64.b64encode(b"Meow").decode("utf-8")
    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.get = AsyncMock(
        return_value=SecretBase(
            secret_key=key, secret=encoded, passphrase=None, expiration_date=None
        )
    )
    mock_db_adapter.delete = AsyncMock(return_value=True)

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
    mock_db_adapter.delete.assert_called_once_with("test_key")


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
    mock_redis_adapter.get = AsyncMock(
        return_value=CacheSecret(
            secret="Meow", passphrase="test_word", expiration_date=300
        )
    )
    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.delete = AsyncMock(return_value=None)

    # when
    res = await delete_secret(
        secret_key="test_key",
        passphrase="test_word",
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
    encoded = base64.b64encode(b"Meow").decode("utf-8")
    mock_redis_adapter = MagicMock(spec=RedisAdapter)
    mock_redis_adapter.delete = AsyncMock(return_value=False)

    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.delete = AsyncMock(return_value=True)
    mock_db_adapter.get = AsyncMock(
        return_value=SecretBase(
            secret_key="test_key", secret=encoded, passphrase=None, expiration_date=None
        )
    )

    # when
    res = await delete_secret(
        secret_key="test_key",
        passphrase=None,
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
    encoded = base64.b64encode(b"Meow").decode("utf-8")
    mock_redis_adapter = MagicMock(spec=RedisAdapter)
    mock_redis_adapter.delete = AsyncMock(return_value=True)
    mock_redis_adapter.get = AsyncMock(
        return_value=CacheSecret(
            secret="Meow", passphrase="test_word", expiration_date=300
        )
    )

    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.delete = AsyncMock(return_value=True)
    mock_db_adapter.get = AsyncMock(
        return_value=SecretBase(
            secret_key="test_key",
            secret=encoded,
            passphrase="test_word",
            expiration_date=300,
        )
    )

    # when
    res = await delete_secret(
        secret_key="test_key",
        passphrase="test_word",
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
    mock_redis_adapter.get = AsyncMock(return_value=None)

    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.delete = AsyncMock(return_value=False)
    mock_db_adapter.get = AsyncMock(return_value=None)

    # when
    with pytest.raises(HTTPException) as exception:
        await delete_secret(
            secret_key="test_key",
            passphrase="test_word",
            db_adapter=mock_db_adapter,
            redis_adapter=mock_redis_adapter,
        )

    # then
    assert exception.value.status_code == 404
    assert exception.value.detail == "secret_not_found"
    mock_redis_adapter.get.assert_called_once_with("test_key")
    mock_db_adapter.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_delete_passphrase_error():
    # given
    encoded = base64.b64encode(b"Meow").decode("utf-8")
    mock_redis_adapter = MagicMock(spec=RedisAdapter)
    mock_redis_adapter.get = AsyncMock(
        return_value=CacheSecret(
            secret=encoded, passphrase="incorrect_word", expiration_date=300
        )
    )
    mock_db_adapter = MagicMock(spec=DBAdapter)
    mock_db_adapter.get = AsyncMock(
        return_value=SecretBase(
            secret_key="test_key",
            secret=encoded,
            passphrase="incorrect_word",
            expiration_date=300,
        )
    )

    # when
    with pytest.raises(HTTPException) as exception:
        await delete_secret(
            secret_key="test_key",
            passphrase="test_word",
            db_adapter=mock_db_adapter,
            redis_adapter=mock_redis_adapter,
        )

    # then
    assert exception.value.status_code == 403
    assert exception.value.detail == "invalid_passphrase"
    mock_redis_adapter.get.assert_called_once_with("test_key")
    mock_db_adapter.get.assert_called_once_with("test_key")
