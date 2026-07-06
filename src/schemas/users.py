from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from models.users import GenderEnum, UserGroupEnum
from security.passwords import password_validator


class UserRegisterRequestSchema(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_validator(cls, password: str):
        return password_validator(password)


class UserRegisterResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime
    is_active: bool


class UserResendActivationSchema(BaseModel):
    email: EmailStr


class UserLoginRequestSchema(UserRegisterRequestSchema):
    pass


class UserMessageSchema(BaseModel):
    message: str


class UserResetRequestSchema(UserResendActivationSchema):
    pass


class UserPasswordChangeRequestSchema(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_validator(cls, new_password: str):
        return password_validator(new_password)


class UserNewPasswordRequestSchema(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_validator(cls, new_password: str):
        return password_validator(new_password)


class UserGroupRequestSchema(BaseModel):
    name: UserGroupEnum


class UserGroupResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: UserGroupEnum


class UserMeRequestSchema(BaseModel):
    first_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, max_length=255)
    avatar: str | None = Field(None, max_length=255)
    gender: GenderEnum | None
    date_of_birth: date | None
    info: str | None


class UserMeResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime
    group: UserGroupResponseSchema
    is_active: bool
    first_name: str | None
    last_name: str | None
    avatar: str | None
    gender: GenderEnum | None
    date_of_birth: date | None
    info: str | None


class UserListItemResponseSchema(UserRegisterResponseSchema):
    group: UserGroupResponseSchema


class UserListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    users: list[UserListItemResponseSchema]
    total_users: int
