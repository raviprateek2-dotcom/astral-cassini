"""Application configuration loaded from environment variables."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global settings for PRO HR."""

    # App
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # OpenAI
    openai_api_key: str = ""

    # LangSmith Tracing
    langchain_tracing_v2: str = "true"
    langchain_api_key: str = ""
    langchain_project: str = "pro-hr"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma_db"

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # LLM Defaults
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.3
    embedding_model: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
