"""Application configuration loaded from environment variables."""

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings for PRO HR."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

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

    # Frontend & CORS
    frontend_url: str = "http://localhost:3000"
    cors_extra_origins: str = Field(
        default="",
        description="Comma-separated extra origins allowed by CORS (e.g. staging URL). FRONTEND_URL is always included.",
    )

    # Auth session cookie (browser)
    auth_cookie_secure: bool = Field(
        default=False,
        description="Set True in production over HTTPS so browsers send Set-Cookie with Secure.",
    )
    auth_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax",
        description="SameSite policy for access_token cookie. Use 'none' only with auth_cookie_secure=true for cross-site setups.",
    )

    # WebSocket (Phase C): short-lived tickets minted via GET /api/auth/ws-ticket
    ws_ticket_expire_minutes: int = Field(
        default=15,
        ge=1,
        le=120,
        description="Lifetime of JWTs used only for WebSocket ?token= (aud prohr-ws).",
    )
    ws_allow_legacy_browser_token: bool = Field(
        default=False,
        description="If True, accept full session access_token in WS query (deprecated). Keep False in production; enable only for temporary rollback.",
    )

    # LLM Defaults
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.3
    embedding_model: str = "text-embedding-3-small"

    # Calendar integration
    calendar_provider: Literal["mock", "google"] = Field(
        default="mock",
        description="Interview calendar provider. 'mock' returns local fake links, 'google' creates real events.",
    )
    google_calendar_id: str = Field(
        default="primary",
        description="Google Calendar ID used when calendar_provider='google'.",
    )
    google_service_account_json: str = Field(
        default="",
        description="Absolute path to Google service account JSON credentials file.",
    )

    @model_validator(mode="after")
    def cookie_none_requires_secure(self) -> "Settings":
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise ValueError(
                "auth_cookie_samesite='none' requires auth_cookie_secure=True (browser requirement)."
            )
        return self


settings = Settings()
