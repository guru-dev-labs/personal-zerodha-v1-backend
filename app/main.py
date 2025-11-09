"""
Personal Zerodha Backend - Main Application Module

This module serves as the entry point for the FastAPI application, handling:
1. Authentication with Zerodha
2. Market data operations
3. Trading operations
4. User profile and holdings management
5. Real-time data streaming

The application uses Redis for caching and session management, and
Supabase for persistent storage.

Environment variables are managed through .env file and Settings class.
"""

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
import logging
import logging.handlers
import sys
from typing import Dict, List
from datetime import datetime
import json

from .config import get_settings, Settings
from .zerodha_client import ZerodhaClient
from .database import get_redis, Database
from .models import UserBase

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.handlers.RotatingFileHandler(
    'app.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Create formatters and add it to handlers
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
console_handler.setFormatter(log_format)
file_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Configure metrics logging
metrics_logger = logging.getLogger("metrics")
metrics_logger.setLevel(logging.INFO)
metrics_handler = logging.handlers.RotatingFileHandler(
    'metrics.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
metrics_format = logging.Formatter('%(asctime)s - %(message)s')
metrics_handler.setFormatter(metrics_format)
metrics_logger.addHandler(metrics_handler)

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Personal Zerodha Backend",
    description="A sophisticated backend service for algorithmic trading with Zerodha",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS middleware for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_zerodha_client(settings: Settings = Depends(get_settings)) -> ZerodhaClient:
    """
    Dependency to get a configured Zerodha client instance.
    Args:
        settings: Application settings from environment
    Returns:
        ZerodhaClient: Configured Zerodha client instance
    Note:
        This is injected into route handlers that need Zerodha access
    """
    logger.debug("Creating new Zerodha client instance")
    return ZerodhaClient(
        api_key=settings.KITE_API_KEY,
        api_secret=settings.KITE_API_SECRET,
        redirect_url=settings.REDIRECT_URL
    )

@app.on_event("startup")
async def startup_event():
    """
    Initialize application resources on startup.
    
    This handler:
    1. Initializes Redis connection pool
    2. Verifies critical environment variables
    3. Sets up logging
    """
    logger.info("Starting application initialization")
    try:
        await Database.init_db()
        logger.info("Redis connection pool initialized successfully")
        
        # Verify critical settings
        settings = get_settings()
        critical_settings = [
            "KITE_API_KEY",
            "KITE_API_SECRET",
            "SUPABASE_URL",
            "SUPABASE_KEY"
        ]
        for setting in critical_settings:
            if not getattr(settings, setting):
                raise ValueError(f"Missing critical setting: {setting}")
        
        logger.info("Critical settings verified successfully")
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.critical(f"Application startup failed: {str(e)}")
        raise

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """
    Root endpoint for health check and basic service information.
    
    Returns:
        dict: Basic service status and information
        
    Note:
        This endpoint is used by monitoring systems to check service health
    """
    logger.debug("Health check request received")
    return {
        "status": "healthy",
        "service": "Personal Zerodha Backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/auth/login", status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    zerodha: ZerodhaClient = Depends(get_zerodha_client)
):
    """
    Get Zerodha login URL for user authentication.
    
    Args:
        request: FastAPI request object for logging client info
        zerodha: Zerodha client instance
        
    Returns:
        dict: Contains the login URL for redirecting users
        
    Note:
        This is the first step in the OAuth flow with Zerodha
    """
    logger.info(
        "Login request received from %s",
        request.client.host if request.client else "unknown"
    )
    try:
        login_url = zerodha.get_login_url()
        logger.debug("Generated login URL successfully")
        
        # Log metrics
        metrics_logger.info(
            "AUTH_REQUEST|%s|%s",
            request.client.host if request.client else "unknown",
            "success"
        )
        
        return {"login_url": login_url}
    except Exception as e:
        logger.error(f"Failed to generate login URL: {str(e)}")
        metrics_logger.info(
            "AUTH_REQUEST|%s|%s",
            request.client.host if request.client else "unknown",
            "failed"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate login URL"
        )

@app.get("/auth/callback", status_code=status.HTTP_200_OK)
async def auth_callback(
    request: Request,
    request_token: str,
    zerodha: ZerodhaClient = Depends(get_zerodha_client),
    redis=Depends(get_redis),
    settings: Settings = Depends(get_settings)
):
    """
    Handle Zerodha authentication callback and establish user session.
    
    This endpoint:
    1. Exchanges request token for access token
    2. Fetches user profile
    3. Stores session in Redis
    4. Returns session details to client
    
    Args:
        request: FastAPI request object
        request_token: Token received from Zerodha after user login
        zerodha: Zerodha client instance
        redis: Redis connection for session storage
        settings: Application settings
        
    Returns:
        dict: Session information including access token and user profile
        
    Raises:
        HTTPException: If authentication fails
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Auth callback received from {client_ip}")
    
    try:
        # Generate session
        logger.debug("Generating session with request token")
        session = zerodha.generate_session(request_token)
        access_token = session["access_token"]
        
        # Get user profile
        logger.debug("Fetching user profile")
        profile = zerodha.get_profile()
        user_id = profile["user_id"]
        
        # Store in Redis with TTL
        logger.debug(f"Storing session for user {user_id}")
        await redis.set(
            f"user:{user_id}:token",
            access_token,
            ex=settings.CACHE_TTL_USER_PROFILE
        )
        
        # Log successful authentication
        logger.info(f"Authentication successful for user {user_id}")
        metrics_logger.info(
            "AUTH_CALLBACK|%s|%s|%s",
            client_ip,
            user_id,
            "success"
        )
        
        return {
            "status": "success",
            "access_token": access_token,
            "profile": profile
        }
    except Exception as e:
        logger.error(f"Auth callback failed: {str(e)}")
        metrics_logger.info(
            "AUTH_CALLBACK|%s|%s|%s",
            client_ip,
            "unknown",
            "failed"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )

from typing import Optional

@app.get("/profile", status_code=status.HTTP_200_OK)
async def get_profile(
    request: Request,
    access_token: Optional[str] = None,
    zerodha: ZerodhaClient = Depends(get_zerodha_client)
) -> Dict:
    """
    Get authenticated user's profile information.
    
    Args:
        request: FastAPI request object
        access_token: Optional access token for Zerodha session
        zerodha: Zerodha client instance
        
    Returns:
        Dict: User profile information
        
    Raises:
        HTTPException: If profile fetch fails
    """
    logger.info("Profile request received")
    try:
        if access_token:
            zerodha.set_access_token(access_token)
        profile = zerodha.get_profile()
        logger.debug(f"Profile fetched successfully for user {profile['user_id']}")
        return profile
    except Exception as e:
        logger.error(f"Profile fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch profile"
        )

from typing import Optional

@app.get("/holdings", status_code=status.HTTP_200_OK)
async def get_holdings(
    request: Request,
    access_token: Optional[str] = None,
    zerodha: ZerodhaClient = Depends(get_zerodha_client),
    redis=Depends(get_redis),
    settings: Settings = Depends(get_settings)
) -> List[Dict]:
    """
    Get user holdings with Redis caching.
    
    This endpoint:
    1. Checks Redis cache for holdings
    2. If not found, fetches from Zerodha
    3. Updates cache with new data
    4. Returns holdings to client
    
    Args:
        request: FastAPI request object
        access_token: Optional access token for Zerodha session
        zerodha: Zerodha client instance
        redis: Redis connection for caching
        settings: Application settings
        
    Returns:
        List[Dict]: User's holdings information
        
    Raises:
        HTTPException: If holdings fetch fails
    """
    try:
        # Set access token if provided
        if access_token:
            zerodha.set_access_token(access_token)
        # Get user profile for cache key
        profile = zerodha.get_profile()
        user_id = profile["user_id"]
        logger.info(f"Holdings request received for user {user_id}")
        # Try to get from cache
        cache_key = f"user:{user_id}:holdings"
        logger.debug(f"Checking cache for holdings with key {cache_key}")
        cached_holdings = await redis.get(cache_key)
        if cached_holdings:
            logger.debug("Holdings found in cache")
            return json.loads(cached_holdings)
        # If not in cache, fetch from Zerodha
        logger.debug("Holdings not in cache, fetching from Zerodha")
        holdings = zerodha.get_holdings()
        # Store in cache
        logger.debug("Updating holdings cache")
        await redis.set(
            cache_key,
            json.dumps(holdings),
            ex=settings.CACHE_TTL_HOLDINGS
        )
        # Log metrics
        metrics_logger.info(
            "HOLDINGS_FETCH|%s|%s|%d",
            user_id,
            "success",
            len(holdings)
        )
        return holdings
    except Exception as e:
        logger.error(f"Failed to fetch holdings: {str(e)}")
        metrics_logger.info(
            "HOLDINGS_FETCH|%s|%s",
            user_id if 'user_id' in locals() else "unknown",
            "failed"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch holdings: {str(e)}"
        )

@app.get("/positions", status_code=status.HTTP_200_OK)
async def get_positions(
    request: Request,
    access_token: Optional[str] = None,
    zerodha: ZerodhaClient = Depends(get_zerodha_client),
    redis=Depends(get_redis),
    settings: Settings = Depends(get_settings)
) -> Dict:
    """
    Get user positions with Redis caching.
    
    This endpoint:
    1. Checks Redis cache for positions
    2. If not found, fetches from Zerodha
    3. Updates cache with new data
    4. Returns positions to client
    
    Args:
        request: FastAPI request object
        access_token: Optional access token for Zerodha session
        zerodha: Zerodha client instance
        redis: Redis connection for caching
        settings: Application settings
        
    Returns:
        Dict: User's positions information
        
    Raises:
        HTTPException: If positions fetch fails
    """
    try:
        # Set access token if provided
        if access_token:
            zerodha.set_access_token(access_token)
        # Get user profile for cache key
        profile = zerodha.get_profile()
        user_id = profile["user_id"]
        logger.info(f"Positions request received for user {user_id}")
        # Try to get from cache
        cache_key = f"user:{user_id}:positions"
        logger.debug(f"Checking cache for positions with key {cache_key}")
        cached_positions = await redis.get(cache_key)
        if cached_positions:
            logger.debug("Positions found in cache")
            return json.loads(cached_positions)
        # If not in cache, fetch from Zerodha
        logger.debug("Positions not in cache, fetching from Zerodha")
        positions = zerodha.get_positions()
        # Store in cache
        logger.debug("Updating positions cache")
        await redis.set(
            cache_key,
            json.dumps(positions),
            ex=settings.CACHE_TTL_POSITIONS
        )
        # Log metrics
        metrics_logger.info(
            "POSITIONS_FETCH|%s|%s|%d",
            user_id,
            "success",
            len(positions.get("net", []))
        )
        return positions
    except Exception as e:
        logger.error(f"Failed to fetch positions: {str(e)}")
        metrics_logger.info(
            "POSITIONS_FETCH|%s|%s",
            user_id if 'user_id' in locals() else "unknown",
            "failed"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch positions: {str(e)}"
        )