from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_ID: int
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/armatdance"
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
