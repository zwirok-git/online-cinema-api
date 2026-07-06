from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AdminMovieCreateSchema(BaseModel):
    name: str = Field(max_length=250)
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: float | None = None
    gross: float | None = None
    description: str
    price: Decimal = Field(max_digits=10, decimal_places=2)
    certification_id: int
    genre_ids: list[int] = []
    star_ids: list[int] = []
    director_ids: list[int] = []


class AdminMovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=250)
    year: int | None = None
    time: int | None = None
    imdb: float | None = None
    votes: int | None = None
    meta_score: float | None = None
    gross: float | None = None
    description: str | None = None
    price: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    certification_id: int | None = None
    genre_ids: list[int] | None = None
    star_ids: list[int] | None = None
    director_ids: list[int] | None = None


class AdminMovieResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: float | None
    gross: float | None
    description: str
    price: Decimal
    certification_id: int
