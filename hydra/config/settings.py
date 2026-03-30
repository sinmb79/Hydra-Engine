from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    hydra_api_key: str = "change-me"
    hydra_profile: str = "lite"
    redis_url: str = "redis://localhost:6379"
    db_url: str = "sqlite:///data/hydra.db"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
