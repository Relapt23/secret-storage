from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uuid
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


class SecretBase(Base):
    __tablename__ = "secret_base"
    secret_key: Mapped[int] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        primary_key=True,
    )
    secret: Mapped[str]
    passphrase: Mapped[str | None] = mapped_column(nullable=True)
    expiration_date: Mapped[int | None] = mapped_column(nullable=True)
