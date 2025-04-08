from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel


class Secret(BaseModel):
    secret: str
    passphrase: str | None = None
    ttl_seconds: int | None = None


@dataclass
class CacheSecret:
    secret: str
    ttl: Optional[int]
