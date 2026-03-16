"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_provider: str = "openai"  # openai / anthropic / deepseek
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""

    # Database
    database_url: str = "sqlite:///data/lifeos.db"
    chroma_persist_dir: str = "./chroma_data"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # Log
    log_level: str = "DEBUG"


settings = Settings()
