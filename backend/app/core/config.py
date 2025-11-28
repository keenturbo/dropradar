from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://dropradar:dropradar_secret@localhost:5432/dropradar"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Keys (will be configured later)
    MOZ_API_KEY: Optional[str] = None
    BARK_API_KEY: Optional[str] = None
    
    # Application
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
