from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SkillRadar API"
    api_prefix: str = "/api/v1"
    database_url: str = (
        "postgresql+psycopg://skillradar:skillradar@localhost:5432/skillradar"
    )

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
