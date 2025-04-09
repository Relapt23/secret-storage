from dataclasses import dataclass
from typing import Optional
from fastapi import HTTPException
from pydantic import BaseModel


class Secret(BaseModel):
    secret: str
    passphrase: str | None = None
    ttl_seconds: int | None = None


@dataclass
class CacheSecret:
    secret: str
    ttl: Optional[int]


class CustomException(HTTPException):
    def __init__(self, detail: str, status_code: int):
        super().__init__(status_code=status_code, detail=detail)
