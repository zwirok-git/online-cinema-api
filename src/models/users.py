import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


if TYPE_CHECKING:
    from models.tokens import (
        ActivationTokenModel,
        PasswordResetTokenModel,
        RefreshTokenModel,
    )


class UserGroupEnum(enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class GenderEnum(enum.Enum):
    MALE = "male"
    FEMALE = "female"


class UserGroupModel(Base):
    __tablename__ = "users_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[UserGroupEnum] = mapped_column(
        Enum(UserGroupEnum),
        nullable=False,
        default=UserGroupEnum.USER,
        unique=True,
    )
    users: Mapped[list["UserModel"]] = relationship(
        "UserModel", back_populates="group"
    )


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("users_groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    group: Mapped["UserGroupModel"] = relationship(
        "UserGroupModel", back_populates="users"
    )

    activation_token: Mapped["ActivationTokenModel" | None] = relationship(
        "ActivationTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reset_token: Mapped["PasswordResetTokenModel" | None] = relationship(
        "PasswordResetTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_token: Mapped[list["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    profile: Mapped[Optional["UserProfileModel"]] = relationship(
        "UserProfileModel", back_populates="user", cascade="all, delete-orphan"
    )


class UserProfileModel(Base):
    __tablename__ = "users_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    first_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gender: Mapped[Optional[GenderEnum]] = mapped_column(
        Enum(GenderEnum), nullable=True
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="profile"
    )
