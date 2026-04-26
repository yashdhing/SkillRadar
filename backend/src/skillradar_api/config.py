from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SQLITE_PATH = Path(__file__).resolve().parents[2] / "skillradar-dev.db"


class Settings(BaseSettings):
    app_name: str = "SkillRadar API"
    api_prefix: str = "/api/v1"
    database_url: str = f"sqlite+pysqlite:///{DEFAULT_SQLITE_PATH}"

    model_config = SettingsConfigDict(
        env_prefix="SKILLRADAR_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def load_settings() -> Settings:
    return Settings()
