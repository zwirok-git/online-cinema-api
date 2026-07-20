from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CartItemCreateRequest(BaseModel):
    movie_id: int


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    name: str
    price: Decimal
    year: int
    genres: list[str]


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    items: list[CartItemResponse]
