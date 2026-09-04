from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ReelsToRoute AI"
    PROJECT_VERSION: str = "1.0.0"
    
    # PostgreSQL connection string (Now loaded from .env)
    DATABASE_URL: str
    
    # JWT Settings (Now loaded from .env)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    
    # AI Service Settings
    GEMINI_API_KEY: Optional[str] = None # Or OPENAI_API_KEY if we change

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
