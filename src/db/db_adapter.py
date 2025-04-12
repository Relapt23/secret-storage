from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models import SecretBase
from typing import Optional
import uuid
from fastapi import Depends
from src.db.db_config import make_session


class DBAdapter:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        secret: str,
        passphrase: Optional[str],
        ttl_seconds: Optional[int],
    ) -> str:
        secret_key = str(uuid.uuid4())
        secret_info = SecretBase(
            secret_key=secret_key,
            secret=secret,
            passphrase=passphrase,
            ttl_seconds=ttl_seconds,
        )

        self.session.add(secret_info)
        await self.session.commit()
        return secret_key

    async def get(self, secret_key: str) -> SecretBase | None:
        query = await self.session.execute(
            select(SecretBase).where(SecretBase.secret_key == secret_key)
        )
        secret = query.scalar_one_or_none()
        return secret

    async def delete(self, secret_key: str) -> bool:
        query = await self.session.execute(
            select(SecretBase).where(SecretBase.secret_key == secret_key)
        )
        secret_obj = query.scalar_one_or_none()
        if not secret_obj:
            return False
        await self.session.delete(secret_obj)
        await self.session.commit()
        return True


def make_db_adapter(session: AsyncSession = Depends(make_session)) -> DBAdapter:
    return DBAdapter(session)
