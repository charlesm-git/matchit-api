from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column

from database import Session
from models.base import Base


class Account(Base):
    __tablename__ = "account"
    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    username: Mapped[str] = mapped_column(
        unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(nullable=False)

    @classmethod
    def get_by_id(cls, db: Session, account_id: int) -> "Account | None":
        return db.get(cls, account_id)

    @classmethod
    def get_by_username(cls, db: Session, username: str) -> "Account | None":
        return db.scalar(select(cls).where(cls.username == username))
