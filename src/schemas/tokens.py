from pydantic import BaseModel, ConfigDict


class TokenPairResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh: str


class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str


class AccessTokenResponseSchema(BaseModel):
    access_token: str


class LogoutRequestSchema(BaseModel):
    refresh_token: str
