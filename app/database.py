from typing import AsyncGenerator
from redis.asyncio import Redis
from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()

class Database:
    supabase: Client = None
    redis: Redis = None
    
    @classmethod
    async def init_db(cls) -> None:
        """Initialize both Supabase and Redis connections"""
        # Initialize Supabase
        cls.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        
        # Initialize Redis
        cls.redis = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True  # Automatically decode responses to Python strings
        )
    
    @classmethod
    async def close_db(cls) -> None:
        """Close database connections"""
        if cls.redis:
            await cls.redis.close()
    
    @classmethod
    async def get_redis(cls) -> Redis:
        """Get Redis connection"""
        if not cls.redis:
            await cls.init_db()
        return cls.redis
    
    @classmethod
    def get_supabase(cls) -> Client:
        """Get Supabase client"""
        if not cls.supabase:
            cls.supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return cls.supabase

# Compatibility functions for existing code
async def init_redis_pool() -> None:
    """Initialize Redis connection pool - compatibility wrapper"""
    await Database.init_db()

async def close_redis_pool() -> None:
    """Close Redis connection pool - compatibility wrapper"""
    await Database.close_db()

# FastAPI dependency for Redis
async def get_redis() -> AsyncGenerator[Redis, None]:
    """Dependency for getting Redis connection"""
    redis_client = await Database.get_redis()
    try:
        yield redis_client
    finally:
        # Connection will be closed when the app shuts down
        pass

# FastAPI dependency for Supabase
def get_supabase() -> Client:
    """Dependency for getting Supabase client"""
    return Database.get_supabase()