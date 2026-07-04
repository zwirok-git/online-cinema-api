import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class PasswordValidatorMixin:
    @field_validator("password")
    @classmethod
    def password_validator(cls, password: str):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        if not re.search(r"[A-Z]", password):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r"[a-z]", password):
            raise ValueError(
                "Password must contain at least one lowercase letter."
            )

        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit.")

        return password


class UserRegisterRequestSchema(PasswordValidatorMixin, BaseModel):
    email: EmailStr
    password: str


class UserRegisterResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime
    is_active: bool


class UserLoginRequestSchema(UserRegisterRequestSchema):
    pass
