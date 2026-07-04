from pydantic import BaseModel, ConfigDict


class TokenPairResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh: str
