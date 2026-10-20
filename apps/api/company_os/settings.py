from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://company:company@localhost:5432/company"
    session_secret: str = ""
    bootstrap_token: str = ""
    app_origin: str = "http://localhost:3000"
    secure_cookies: bool = True
    founder_email: str = "traisorn.th@gmail.com"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_tls: bool = False
    temporal_api_key: str = ""
    model_provider: str = "openai"
    openrouter_api_key: str = ""
    openai_api_key: str = ""
    research_model: str = "gpt-4.1-mini"
    codex_provider: str = "openai"
    codex_model: str = "gpt-5-codex"
    codex_input_usd_per_million: float = 0
    codex_output_usd_per_million: float = 0
    daytona_api_key: str = ""
    daytona_api_url: str = "https://app.daytona.io/api"
    daytona_snapshot: str = ""
    github_token: str = Field(default="", validation_alias=AliasChoices("GITHUB_TOKEN", "GH_TOKEN"))
    github_repository: str = ""
    artifact_backend: str = "s3"
    artifact_directory: str = ".local/artifacts"
    artifact_encryption_key: str = ""
    artifact_access_key_id: str = ""
    artifact_secret_access_key: str = ""
    s3_bucket: str = ""
    s3_endpoint_url: str = ""
    gmail_access_token: str = ""
    gmail_refresh_token: str = ""
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    email_send_authorized: bool = False
    stripe_webhook_secret: str = ""
    sandbox_thb_per_minute: float = 0
    sandbox_price_observed_at: str = ""
    model_gateway_public_url: str = ""
    model_input_usd_per_million: float = 0
    model_output_usd_per_million: float = 0
    thb_per_usd: float = 0
    fx_observed_at: str = ""
    telemetry_enabled: bool = False
    research_daily_hour_utc: int = 2
    worker_poll_seconds: int = 15
    runtime: str = "development"

    @field_validator("database_url", mode="before")
    @classmethod
    def use_installed_postgres_driver(cls, value):
        if isinstance(value, str):
            for prefix in ("postgres://", "postgresql://"):
                if value.startswith(prefix):
                    return "postgresql+psycopg://" + value[len(prefix) :]
        return value


@lru_cache
def settings():
    return Settings()
