from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    
    # Zerodha Configuration
    KITE_API_KEY: str
    KITE_API_SECRET: str
    
    # Application Configuration
    APP_NAME: str = "Personal Zerodha"
    DEBUG: bool = False
    
    # Cache Configuration
    CACHE_TTL_QUOTES: int = 1  # 1 second for market quotes
    CACHE_TTL_HOLDINGS: int = 300  # 5 minutes for holdings
    CACHE_TTL_USER_PROFILE: int = 3600  # 1 hour for user profile
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
