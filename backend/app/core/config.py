"""Application configuration loaded from environment variables."""

from __future__ import annotations

import json
from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_provider: str = "openai"  # openai / anthropic / deepseek / gemini / newapi
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    gemini_api_key: str = ""

    # NEWAPI (OpenAI-compatible gateway)
    newapi_api_key: str = ""
    newapi_base_url: str = ""  # e.g. "https://your-gateway.com/v1"
    newapi_group: str = ""  # NEWAPI channel group, e.g. "Other"
    newapi_headers: str = ""  # Extra headers as JSON, e.g. '{"User-Agent": "Mozilla/5.0"}'

    # Per-caller LLM overrides (JSON string)
    # Format: {"caller_name": {"provider": "newapi", "model": "gpt-4o", "group": "Other", "headers": {"User-Agent": "..."}}, ...}
    llm_caller_overrides: str = ""

    @cached_property
    def caller_overrides(self) -> dict[str, dict[str, str]]:
        if not self.llm_caller_overrides:
            return {}
        return json.loads(self.llm_caller_overrides)

    # Database
    database_url: str = "sqlite:///data/lifeos.db"
    chroma_persist_dir: str = "./chroma_data"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # Log
    log_level: str = "DEBUG"


settings = Settings()
