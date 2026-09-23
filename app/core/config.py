from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    app_name: str = "HATTORI AI Assistant"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://hattori:hattori@localhost:5432/hattori"
    altegio_base_url: str | None = None
    altegio_api_token: SecretStr | None = None
    altegio_user_token: SecretStr | None = None
    altegio_branch_id: str | None = None
    altegio_accept_header: str = "application/json"
    altegio_timeout_seconds: float = 10.0
    altegio_services_path: str | None = None
    altegio_masters_path: str | None = None
    altegio_available_slots_path: str | None = None
    altegio_create_booking_path: str | None = None
    altegio_cancel_booking_path: str | None = None
    altegio_cancel_booking_method: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
