from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Environment Configuration
    ENVIRONMENT: str = "development"  # development, staging, production
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_URL: str | None = None  # Optional: override full Redis URL

    # Zerodha Configuration
    KITE_API_KEY: str
    KITE_API_SECRET: str
    REDIRECT_URL: str | None = None  # Will be auto-generated if not provided

    # Application Configuration
    APP_NAME: str = "Personal Zerodha"
    DEBUG: bool = False

    # Cache Configuration
    CACHE_TTL_QUOTES: int = 1  # 1 second for market quotes
    CACHE_TTL_HOLDINGS: int = 300  # 5 minutes for holdings
    CACHE_TTL_POSITIONS: int = 60  # 1 minute for positions (more volatile)
    CACHE_TTL_USER_PROFILE: int = 3600  # 1 hour for user profile

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Auto-generate Redis URL if not provided
        if not self.REDIS_URL:
            auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
            self.REDIS_URL = f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def get_redirect_url(self) -> str:
        """Generate redirect URL based on current configuration"""
        if self.REDIRECT_URL:
            return self.REDIRECT_URL

        protocol = "https" if (self.is_production or self.is_staging) else "http"
        host = self.APP_HOST
        port = "" if ((self.is_production or self.is_staging) or self.APP_PORT == 80 or (protocol == "https" and self.APP_PORT == 443)) else f":{self.APP_PORT}"
        return f"{protocol}://{host}{port}/auth/callback"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT == "staging"

    @property
    def base_url(self) -> str:
        protocol = "https" if self.is_production else "http"
        host = self.APP_HOST
        port = "" if (self.is_production or self.APP_PORT == 80 or (protocol == "https" and self.APP_PORT == 443)) else f":{self.APP_PORT}"
        return f"{protocol}://{host}{port}"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
