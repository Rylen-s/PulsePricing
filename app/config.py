from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    redis_url: str | None = None
    database_url: str | None = None
    alpha_vantage_api_key: str | None = None
    simulation_paths: int = 10_000
    simulation_horizon_days: int = 21


@lru_cache
def get_settings() -> Settings:
    return Settings()
