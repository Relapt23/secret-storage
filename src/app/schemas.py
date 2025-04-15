from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel


class Secret(BaseModel):
    secret: str
    passphrase: str | None = None
    expiration_date: int | None = None


@dataclass
class CacheSecret:
    secret: str
    passphrase: Optional[str]
    expiration_date: Optional[int]


class SecretInfo(BaseModel):
    secret: str


class SecretKeyInfo(BaseModel):
    secret_key: str


class DeletedSecret(BaseModel):
    status: str
