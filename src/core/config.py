from datetime import timedelta

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    POSTGRES_DB: str = "movies_db"
    POSTGRES_PASSWORD: str = "some_password"
    POSTGRES_USER: str = "postgres"
    POSTGRES_DB_PORT: int = 5432
    POSTGRES_HOST: str = "localhost"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}"
        )

    STRIPE_SECRET_KEY: str = "sk_test_placeholder"
    STRIPE_WEBHOOK_SECRET: str | None = None
    BASE_URL: str = "http://localhost:8000"

    TOKEN_SECRET_KEY: str = "UuNi2QtnGzRdGIJmsRURVuQFthrwsr1EZu8fOomLQTZ"
    TOKEN_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE: timedelta = timedelta(days=1)
    REFRESH_TOKEN_EXPIRE: timedelta = timedelta(days=30)

    API_V1_PREFIX: str = "/api/v1"

    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = False
    EMAIL_FROM: str = "no-reply@online-cinema.com"

    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    MINIO_ENDPOINT_URL: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_NAME: str = "avatars"
    MINIO_PUBLIC_URL: str = "http://minio:9000/avatars"


settings = Settings()
