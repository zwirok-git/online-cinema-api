import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    POSTGRES_DB: str = os.getenv("DB_USER", "test_user")
    POSTGRES_PASSWORD: str = os.getenv("DB_PASSWORD", "test_password")
    POSTGRES_USER: str = os.getenv("DB_HOST", "test_host")
    POSTGRES_DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    POSTGRES_HOST: str = os.getenv("DB_NAME", "test_db")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_DB}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_USER}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_HOST}"
        )

    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str | None = None


settings = Settings()
