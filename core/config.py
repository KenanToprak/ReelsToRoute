from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ReelsToRoute AI"
    PROJECT_VERSION: str = "1.0.0"
    
    # PostgreSQL connection string
    # We are using 'postgres' user with 'Postgrekenan' password as established in the previous project.
    # A new database named 'reels_route_db' should be created.
    DATABASE_URL: str = "postgresql://postgres:Postgrekenan@localhost:5432/reels_route_db"
    
    # JWT Settings
    SECRET_KEY: str = "super_secret_reels_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    
    # AI Service Settings
    GEMINI_API_KEY: Optional[str] = None # Or OPENAI_API_KEY if we change

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
