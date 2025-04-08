from sqlalchemy.ext.asyncio import AsyncSession
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

    def get(self, secret_key: str) -> str | None:
        pass

    def delete(self, secret_key: str) -> bool:
        pass


def make_db_adapter(session: AsyncSession = Depends(make_session)) -> DBAdapter:
    return DBAdapter(session)
