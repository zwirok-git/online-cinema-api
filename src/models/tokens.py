from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


if TYPE_CHECKING:
    from models.users import UserModel


class TokenBase(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )


class ActivationTokenModel(TokenBase):
    __tablename__ = "activation_token"

    user: Mapped["UserModel"] = relationship(back_populates="activation_token")


class PasswordResetTokenModel(TokenBase):
    __tablename__ = "reset_token"

    user: Mapped["UserModel"] = relationship(back_populates="reset_token")


class RefreshTokenModel(TokenBase):
    __tablename__ = "refresh_token"

    user: Mapped["UserModel"] = relationship(back_populates="refresh_token")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
