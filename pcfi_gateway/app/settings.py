from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"
    request_timeout_seconds: float = 30.0

    pcfi_policy_path: str = "policies/default_policy.yaml"

    class Config:
        # Use field-name-based env vars, e.g.:
        #   groq_api_key -> GROQ_API_KEY
        #   groq_model   -> GROQ_MODEL
        env_prefix = ""
        env_file = ".env"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

