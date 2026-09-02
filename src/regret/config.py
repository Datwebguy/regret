from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    regret_env: str = "development"
    regret_secret_key: str = Field(default="")
    regret_encryption_key: str = Field(default="")
    regret_public_url: str = "http://127.0.0.1:8000"
    regret_cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    regret_database_url: str = "sqlite:///./data/regret.db"

    regret_default_trading_environment: str = "paper"
    regret_live_trading_enabled: bool = False

    alpaca_oauth_client_id: str = ""
    alpaca_oauth_client_secret: str = ""
    alpaca_oauth_redirect_uri: str = "http://127.0.0.1:8000/api/alpaca/callback"

    # Development-only paper credentials. Never used as a shared multi-user
    # trading identity. Never sent to the browser.
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""

    alpaca_data_api_key_id: str = ""
    alpaca_data_api_secret_key: str = ""
    alpaca_data_feed: str = "iex"

    regret_llm_base_url: str = ""
    regret_llm_api_key: str = ""
    regret_llm_model: str = ""

    featherless_api_key: str = ""
    featherless_model: str = "meta-llama/Llama-3.3-70B-Instruct"
    featherless_base_url: str = "https://api.featherless.ai/v1"

    regret_session_cookie: str = "regret_session"
    regret_session_ttl_hours: int = 168
    regret_approval_ttl_seconds: int = 300
    regret_quote_max_age_seconds: int = 60
    regret_bar_max_age_seconds: int = 900

    regret_login_fail_limit_email: int = 5
    regret_login_fail_limit_ip: int = 30
    regret_login_window_seconds: int = 900
    regret_register_limit_ip: int = 8
    regret_register_window_seconds: int = 3600

    @field_validator("regret_default_trading_environment")
    @classmethod
    def _env_ok(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"paper", "live"}:
            raise ValueError("REGRET_DEFAULT_TRADING_ENVIRONMENT must be paper or live")
        return normalized

    @property
    def is_production(self) -> bool:
        return self.regret_env.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [part.strip() for part in self.regret_cors_origins.split(",") if part.strip()]
        public = (self.regret_public_url or "").rstrip("/")
        if public and public not in origins:
            origins.append(public)
        return origins

    @property
    def oauth_configured(self) -> bool:
        return bool(self.alpaca_oauth_client_id and self.alpaca_oauth_client_secret)

    @property
    def platform_market_data_configured(self) -> bool:
        return bool(self.market_data_key_id and self.market_data_secret)

    @property
    def market_data_key_id(self) -> str:
        return self.alpaca_data_api_key_id or self.alpaca_api_key

    @property
    def market_data_secret(self) -> str:
        return self.alpaca_data_api_secret_key or self.alpaca_secret_key

    @property
    def development_paper_keys_configured(self) -> bool:
        return bool(self.alpaca_api_key and self.alpaca_secret_key)

    @property
    def llm_configured(self) -> bool:
        return bool((self.regret_llm_api_key and self.regret_llm_model) or self.featherless_api_key)

    @property
    def effective_llm_api_key(self) -> str:
        return self.featherless_api_key or self.regret_llm_api_key

    @property
    def effective_llm_base_url(self) -> str:
        if self.featherless_api_key:
            return self.featherless_base_url
        return self.regret_llm_base_url or "https://api.featherless.ai/v1"

    @property
    def effective_llm_model(self) -> str:
        if self.featherless_api_key:
            return self.featherless_model
        return self.regret_llm_model or "meta-llama/Llama-3.3-70B-Instruct"

    def require_secret_key(self) -> str:
        if not self.regret_secret_key or self.regret_secret_key.startswith("replace-"):
            if self.is_production:
                raise RuntimeError("REGRET_SECRET_KEY must be set in production")
        return self.regret_secret_key or "dev-only-insecure-secret-change-me"

    def sqlite_path(self) -> Path | None:
        url = self.regret_database_url
        if not url.startswith("sqlite"):
            return None
        raw = url.split(":///", 1)[-1]
        return Path(raw)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
