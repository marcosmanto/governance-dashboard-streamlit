from datetime import timedelta

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Ambiente
    ENV: str = "dev"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DB_BACKEND: str = "sqlite"
    DB_DSN: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Derived helpers
ACCESS_TOKEN_EXPIRE = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_TOKEN_EXPIRE = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
