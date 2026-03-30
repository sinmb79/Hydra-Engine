import warnings
from functools import lru_cache
from pydantic import field_validator
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

    @field_validator("hydra_api_key")
    @classmethod
    def api_key_must_not_be_default(cls, v: str) -> str:
        if v == "change-me":
            warnings.warn(
                "[HYDRA] HYDRA_API_KEY가 기본값 'change-me'로 설정되어 있습니다. "
                ".env 파일에서 안전한 값으로 변경하세요.",
                stacklevel=2,
            )
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
