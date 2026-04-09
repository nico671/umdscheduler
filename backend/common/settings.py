import os
from functools import lru_cache
from typing import Any, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

load_dotenv()

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def _parse_bool(value: Optional[str], *, default: bool) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False

    raise ValueError(
        f"Invalid boolean value '{value}'. Use one of: "
        f"{', '.join(sorted(_TRUE_VALUES | _FALSE_VALUES))}."
    )


def _parse_int(value: Optional[str], *, default: int) -> int:
    if value is None or value.strip() == "":
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer value '{value}'.") from exc


def _parse_cors_origins(value: Optional[str]) -> List[str]:
    if not value:
        return ["https://umdscheduler.vercel.app"]

    origins = [origin.strip().rstrip("/") for origin in value.split(",")]
    return [origin for origin in origins if origin]


class RuntimeSettings(BaseModel):
    app_env: str = Field(default="development")
    cors_origins: List[str] = Field(
        default_factory=lambda: ["https://umdscheduler.vercel.app"]
    )
    cors_allow_credentials: bool = True

    database_url: Optional[str] = None
    db_ssl_mode: str = "require"
    db_pool_min: int = Field(default=1, ge=1, le=50)
    db_pool_max: int = Field(default=20, ge=1, le=100)
    db_connect_timeout: int = Field(default=10, ge=1, le=60)
    db_keepalives: int = Field(default=1, ge=0, le=1)
    db_keepalives_idle: int = Field(default=30, ge=1, le=3600)
    db_keepalives_interval: int = Field(default=10, ge=1, le=300)
    db_keepalives_count: int = Field(default=5, ge=1, le=20)

    api_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    api_rate_limit_global_per_ip: int = Field(default=400, ge=1, le=5000)
    api_rate_limit_global_burst: int = Field(default=100, ge=0, le=5000)
    api_rate_limit_schedules_per_ip: int = Field(default=8, ge=1, le=200)
    api_rate_limit_schedules_burst: int = Field(default=2, ge=0, le=200)
    api_schedule_max_body_bytes: int = Field(default=64_000, ge=1024, le=1_048_576)

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"development", "staging", "production", "test"}
        if normalized not in allowed:
            raise ValueError(
                f"APP_ENV must be one of {sorted(allowed)}, got '{value}'."
            )
        return normalized

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("CORS_ORIGINS must include at least one origin.")

        normalized: List[str] = []
        seen = set()
        for origin in value:
            candidate = origin.strip().rstrip("/")
            if not candidate:
                continue
            if not (
                candidate.startswith("http://") or candidate.startswith("https://")
            ):
                raise ValueError(
                    f"Invalid CORS origin '{origin}'. Expected http:// or https:// origin."
                )
            if candidate in seen:
                continue
            seen.add(candidate)
            normalized.append(candidate)

        if not normalized:
            raise ValueError("CORS_ORIGINS must include at least one valid origin.")

        return normalized

    @model_validator(mode="after")
    def validate_pool_bounds(self):
        if self.db_pool_max < self.db_pool_min:
            raise ValueError(
                "DB_POOL_MAX must be greater than or equal to DB_POOL_MIN."
            )

        if self.api_rate_limit_schedules_per_ip > self.api_rate_limit_global_per_ip:
            raise ValueError(
                "API_RATE_LIMIT_SCHEDULES_PER_IP cannot exceed API_RATE_LIMIT_GLOBAL_PER_IP."
            )

        return self


def _build_settings_payload() -> dict[str, Any]:
    return {
        "app_env": os.getenv("APP_ENV", "development"),
        "cors_origins": _parse_cors_origins(os.getenv("CORS_ORIGINS")),
        "cors_allow_credentials": _parse_bool(
            os.getenv("CORS_ALLOW_CREDENTIALS"), default=True
        ),
        "database_url": os.getenv("DATABASE_URL"),
        "db_ssl_mode": os.getenv("DB_SSL_MODE", "require"),
        "db_pool_min": _parse_int(os.getenv("DB_POOL_MIN"), default=1),
        "db_pool_max": _parse_int(os.getenv("DB_POOL_MAX"), default=20),
        "db_connect_timeout": _parse_int(os.getenv("DB_CONNECT_TIMEOUT"), default=10),
        "db_keepalives": _parse_int(os.getenv("DB_KEEPALIVES"), default=1),
        "db_keepalives_idle": _parse_int(os.getenv("DB_KEEPALIVES_IDLE"), default=30),
        "db_keepalives_interval": _parse_int(
            os.getenv("DB_KEEPALIVES_INTERVAL"), default=10
        ),
        "db_keepalives_count": _parse_int(os.getenv("DB_KEEPALIVES_COUNT"), default=5),
        "api_rate_limit_window_seconds": _parse_int(
            os.getenv("API_RATE_LIMIT_WINDOW_SECONDS"), default=60
        ),
        "api_rate_limit_global_per_ip": _parse_int(
            os.getenv("API_RATE_LIMIT_GLOBAL_PER_IP"), default=400
        ),
        "api_rate_limit_global_burst": _parse_int(
            os.getenv("API_RATE_LIMIT_GLOBAL_BURST"), default=100
        ),
        "api_rate_limit_schedules_per_ip": _parse_int(
            os.getenv("API_RATE_LIMIT_SCHEDULES_PER_IP"), default=8
        ),
        "api_rate_limit_schedules_burst": _parse_int(
            os.getenv("API_RATE_LIMIT_SCHEDULES_BURST"), default=2
        ),
        "api_schedule_max_body_bytes": _parse_int(
            os.getenv("API_SCHEDULE_MAX_BODY_BYTES"), default=64_000
        ),
    }


@lru_cache(maxsize=1)
def get_settings() -> RuntimeSettings:
    try:
        return RuntimeSettings(**_build_settings_payload())
    except (ValidationError, ValueError) as exc:
        raise RuntimeError(f"Invalid runtime configuration: {exc}") from exc
