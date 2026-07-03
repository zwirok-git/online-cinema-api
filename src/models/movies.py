from __future__ import annotations

import enum
import uuid as uuid_pkg
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DECIMAL,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


'''Це потім я приберу. Нагадування додати форід кі там де юзер айді'''



class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        secondary="movie_genres", back_populates="genres"
    )


class StarModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        secondary="movie_stars", back_populates="stars"
    )


class DirectorModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        secondary="movie_directors", back_populates="directors"
    )


class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(back_populates="certification")


class MovieGenreModel(Base):
    __tablename__ = "movie_genres"

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True
    )


class MovieStarModel(Base):
    __tablename__ = "movie_stars"

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    star_id: Mapped[int] = mapped_column(
        ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True
    )


class MovieDirectorModel(Base):
    __tablename__ = "movie_directors"

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    director_id: Mapped[int] = mapped_column(
        ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True
    )


class MovieModel(Base):
    __tablename__ = "movies"
    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="uq_movie_name_year_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid_pkg.uuid4
    )
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    time: Mapped[int] = mapped_column(nullable=False)
    imdb: Mapped[float] = mapped_column(nullable=False)
    votes: Mapped[int] = mapped_column(nullable=False)
    meta_score: Mapped[float | None] = mapped_column(nullable=True)
    gross: Mapped[float | None] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)

    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id"), nullable=False
    )
    certification: Mapped["CertificationModel"] = relationship(back_populates="movies")

    genres: Mapped[list["GenreModel"]] = relationship(
        secondary="movie_genres", back_populates="movies"
    )
    stars: Mapped[list["StarModel"]] = relationship(
        secondary="movie_stars", back_populates="movies"
    )
    directors: Mapped[list["DirectorModel"]] = relationship(
        secondary="movie_directors", back_populates="movies"
    )

    comments: Mapped[list["CommentModel"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
    likes: Mapped[list["MovieLikeModel"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
    favorites: Mapped[list["FavoriteModel"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
    ratings: Mapped[list["MovieRatingModel"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )


class LikeStatus(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class MovieLikeModel(Base):
    __tablename__ = "movie_likes"
    __table_args__ = (
        UniqueConstraint("movie_id", "user_id", name="uq_movie_like_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(nullable=False)  # Тута фор кі
    status: Mapped[LikeStatus] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    movie: Mapped["MovieModel"] = relationship(back_populates="likes")


class FavoriteModel(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("movie_id", "user_id", name="uq_favorite_movie_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(nullable=False)  # Тута фор кі
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    movie: Mapped["MovieModel"] = relationship(back_populates="favorites")


class MovieRatingModel(Base):
    __tablename__ = "movie_ratings"
    __table_args__ = (
        UniqueConstraint("movie_id", "user_id", name="uq_rating_movie_user"),
        CheckConstraint("rating BETWEEN 1 AND 10", name="ck_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(nullable=False)  # Тута фор кі
    rating: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    movie: Mapped["MovieModel"] = relationship(back_populates="ratings")


class CommentModel(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(nullable=False)  # Тута фор кі
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    movie: Mapped["MovieModel"] = relationship(back_populates="comments")
    parent: Mapped["CommentModel | None"] = relationship(
        remote_side="CommentModel.id", back_populates="replies"
    )
    replies: Mapped[list["CommentModel"]] = relationship(back_populates="parent")
    likes: Mapped[list["CommentLikeModel"]] = relationship(
        back_populates="comment", cascade="all, delete-orphan"
    )


class CommentLikeModel(Base):
    __tablename__ = "comment_likes"
    __table_args__ = (
        UniqueConstraint("comment_id", "user_id", name="uq_comment_like_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(nullable=False) # Тута фор кі
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    comment: Mapped["CommentModel"] = relationship(back_populates="likes")
