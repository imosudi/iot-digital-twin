"""Configuration settings for TwinField Digital Twin API service."""

import os
from dataclasses import dataclass, field
from typing import List


def _get_cors_origins() -> List[str]:
    default_origins = (
        "http://localhost:5173,http://localhost:3000,"
        "https://twinfield.regenova.cloud,https://regenova.cloud"
    )
    raw = os.getenv("TWINFIELD_CORS_ORIGINS", os.getenv("CORS_ORIGINS", default_origins))
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("TWINFIELD_ENV", "development")
    database_url: str = os.getenv(
        "TWINFIELD_DATABASE_URL",
        os.getenv("DATABASE_URL", "sqlite:///./iot_digital_twin.db"),
    )
    api_host: str = os.getenv("TWINFIELD_API_HOST", os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = int(os.getenv("TWINFIELD_API_PORT", os.getenv("API_PORT", "9000")))
    cors_origins: List[str] = field(default_factory=_get_cors_origins)
    log_level: str = os.getenv("TWINFIELD_LOG_LEVEL", "INFO")
    secret_key: str = os.getenv(
        "TWINFIELD_SECRET_KEY",
        os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod"),
    )


settings = Settings()
