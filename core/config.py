import json
from typing import Annotated, Any, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ReelsToRoute AI"
    PROJECT_VERSION: str = "1.0.0"

    # Database connection string (loaded from environment / .env)
    DATABASE_URL: str

    # JWT Settings (loaded from environment / .env)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # AI Service Settings
    GEMINI_API_KEY: Optional[str] = None

    # CORS allowed origins (comma-separated string or JSON list)
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("DATABASE_URL", "SECRET_KEY")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return value

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    raise ValueError("ALLOWED_ORIGINS JSON must be a list of origins")
                origins = [str(item).strip() for item in parsed if str(item).strip()]
            else:
                origins = [item.strip() for item in raw.split(",") if item.strip()]
        elif isinstance(value, (list, tuple)):
            origins = [str(item).strip() for item in value if str(item).strip()]
        else:
            raise ValueError("ALLOWED_ORIGINS must be a list or comma-separated string")

        if "*" in origins:
            raise ValueError("Wildcard '*' is not allowed in ALLOWED_ORIGINS when credentials are enabled")
        return origins


settings = Settings()
