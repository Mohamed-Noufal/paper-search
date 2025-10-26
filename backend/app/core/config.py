from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Research Paper Search API"
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # External APIs
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None
    OPENALEX_EMAIL: Optional[str] = None  # For polite pool access
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour
    
    # Search Settings
    DEFAULT_SEARCH_LIMIT: int = 50
    MAX_SEARCH_LIMIT: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()