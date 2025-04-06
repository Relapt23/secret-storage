from pydantic import BaseModel


class Secret(BaseModel):
    secret: str
    passphrase: str | None = None
    ttl_seconds: int | None = None
