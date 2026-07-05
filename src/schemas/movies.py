import enum
import uuid as uuid_pkg
from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.movies import LikeStatus


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class GenreWithCountSchema(GenreSchema):
    movies_count: int


class StarSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class DirectorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class CertificationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class MovieBaseSchema(BaseModel):
    name: str = Field(..., max_length=250)
    year: int
    time: int = Field(..., gt=0)
    imdb: float = Field(..., ge=0, le=10)
    votes: int = Field(..., ge=0)
    meta_score: float | None = Field(None, ge=0, le=100)
    gross: float | None = None
    description: str
    price: Decimal | None = Field(None, ge=0)
    certification_id: int


class MovieCreateSchema(MovieBaseSchema):
    genre_ids: list[int] = Field(default_factory=list)
    star_ids: list[int] = Field(default_factory=list)
    director_ids: list[int] = Field(default_factory=list)


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(None, max_length=250)
    year: int | None = None
    time: int | None = Field(None, gt=0)
    imdb: float | None = Field(None, ge=0, le=10)
    votes: int | None = Field(None, ge=0)
    meta_score: float | None = Field(None, ge=0, le=100)
    gross: float | None = None
    description: str | None = None
    price: Decimal | None = Field(None, ge=0)
    certification_id: int | None = None
    genre_ids: list[int] | None = None
    star_ids: list[int] | None = None
    director_ids: list[int] | None = None


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    uuid: uuid_pkg.UUID
    name: str
    year: int
    imdb: float
    price: Decimal | None


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    uuid: uuid_pkg.UUID
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: float | None
    gross: float | None
    description: str
    price: Decimal | None
    certification: CertificationSchema
    genres: list[GenreSchema]
    stars: list[StarSchema]
    directors: list[DirectorSchema]
    likes_count: int = 0
    dislikes_count: int = 0
    average_rating: float | None = None


ItemT = TypeVar("ItemT", bound=BaseModel)


class PaginatedResponseSchema(BaseModel, Generic[ItemT]):
    items: list[ItemT]
    total: int
    page: int
    per_page: int
    total_pages: int


class MovieSortField(str, enum.Enum):
    PRICE = "price"
    RELEASE_DATE = "year"
    POPULARITY = "votes"
    IMDB = "imdb"


class SortOrder(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


class MovieFilterParams(BaseModel):
    year: int | None = None
    year_from: int | None = None
    year_to: int | None = None
    imdb_from: float | None = Field(None, ge=0, le=10)
    imdb_to: float | None = Field(None, ge=0, le=10)
    genre_id: int | None = None

    @field_validator("imdb_to")
    @classmethod
    def check_imdb_range(cls, v: float | None, info) -> float | None:
        imdb_from = info.data.get("imdb_from")
        if v is not None and imdb_from is not None and v < imdb_from:
            raise ValueError("imdb_to can't be less than imdb_from")
        return v


class MovieSearchParams(BaseModel):
    query: str = Field(..., min_length=1, max_length=250)


class MovieLikeCreateSchema(BaseModel):
    status: LikeStatus


class MovieRatingCreateSchema(BaseModel):
    rating: int = Field(..., ge=1, le=10)


class CommentCreateSchema(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    parent_id: int | None = None


class CommentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    user_id: int
    parent_id: int | None
    text: str
    created_at: datetime
    replies: list["CommentSchema"] = Field(default_factory=list)
    likes_count: int = 0


CommentSchema.model_rebuild()
