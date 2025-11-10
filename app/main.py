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
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import logging.handlers
import sys
from typing import Dict
from datetime import datetime
import asyncio

from .config import get_settings, Settings
from .zerodha_client import ZerodhaClient
from .database import get_redis, init_redis_pool
from .short_sell_scanner import ShortSellScanner
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

async def get_zerodha_client(
    request: Request,
    redis=Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> ZerodhaClient:
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
    # Create client and attempt to attach an access token from the request
    client = ZerodhaClient(
        api_key=settings.KITE_API_KEY,
        api_secret=settings.KITE_API_SECRET,
        redirect_url=settings.get_redirect_url()
    )

    # Prefer Authorization header (Bearer) if provided
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(None, 1)[1]
        client.set_access_token(token)
        logger.debug("Attached access token from Authorization header (truncated): %s", token[:8])
        return client

    # Otherwise look for a session cookie with user id and fetch token from Redis
    user_cookie = request.cookies.get("session_user")
    if user_cookie:
        try:
            stored = await redis.get(f"user:{user_cookie}:token")
            if stored:
                client.set_access_token(stored)
                logger.debug("Attached access token from Redis for user %s (truncated): %s", user_cookie, stored[:8])
            else:
                logger.debug("No token found in Redis for user %s", user_cookie)
        except Exception:
            # If Redis is unavailable, leave client unauthenticated
            logger.exception("Failed to fetch token from Redis for user %s", user_cookie)

    return client

# Global scanner instance
short_sell_scanner = None

def get_short_sell_scanner(zerodha: ZerodhaClient = Depends(get_zerodha_client)) -> ShortSellScanner:
    """Get the global short sell scanner instance"""
    global short_sell_scanner
    if short_sell_scanner is None:
        short_sell_scanner = ShortSellScanner(zerodha)
    return short_sell_scanner

@app.on_event("startup")
async def startup_event():
    """
    Initialize application resources on startup.
    
    This handler:
    1. Initializes Redis connection pool
    2. Verifies critical environment variables
    3. Sets up logging
    4. Initializes short sell scanner
    """
    logger.info("Starting application initialization")
    try:
        await init_redis_pool()
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
        
        # Initialize short sell scanner
        global short_sell_scanner
        zerodha_client = ZerodhaClient(
            api_key=settings.KITE_API_KEY,
            api_secret=settings.KITE_API_SECRET,
            redirect_url=settings.get_redirect_url()
        )
        short_sell_scanner = ShortSellScanner(zerodha_client)
        await short_sell_scanner.initialize()
        
        # Start background scanning
        asyncio.create_task(short_sell_scanner.start_continuous_scanning())
        logger.info("Short sell scanner initialized and started")
        
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

        # Return session and set an HttpOnly cookie so subsequent requests
        # from the browser can be associated with this user and retrieve token
        resp = JSONResponse({
            "status": "success",
            "access_token": access_token,
            "profile": profile
        })
        # Cookie lifetime mirrors our profile TTL
        resp.set_cookie(
            key="session_user",
            value=user_id,
            httponly=True,
            secure=settings.is_production,
            samesite="lax",
            max_age=settings.CACHE_TTL_USER_PROFILE
        )

        return resp
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

@app.get("/profile", status_code=status.HTTP_200_OK)
async def get_profile(
    request: Request,
    zerodha: ZerodhaClient = Depends(get_zerodha_client)
) -> Dict:
    """
    Get authenticated user's profile information.
    
    Args:
        request: FastAPI request object
        zerodha: Zerodha client instance
        
    Returns:
        Dict: User profile information
        
    Raises:
        HTTPException: If profile fetch fails
    """
    logger.info("Profile request received")
    try:
        profile = zerodha.get_profile()
        logger.debug(f"Profile fetched successfully for user {profile['user_id']}")
        return profile
    except Exception as e:
        logger.error(f"Profile fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch profile"
        )

@app.get("/holdings", status_code=status.HTTP_200_OK)
async def get_holdings(
    request: Request,
    zerodha: ZerodhaClient = Depends(get_zerodha_client),
    redis=Depends(get_redis),
    settings: Settings = Depends(get_settings)
) -> Dict:
    """
    Get user holdings with Redis caching.
    
    This endpoint:
    1. Checks Redis cache for holdings
    2. If not found, fetches from Zerodha
    3. Updates cache with new data
    4. Returns holdings to client
    
    Args:
        request: FastAPI request object
        zerodha: Zerodha client instance
        redis: Redis connection for caching
        settings: Application settings
        
    Returns:
        Dict: User's holdings information
        
    Raises:
        HTTPException: If holdings fetch fails
    """
    try:
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
            return cached_holdings
        
        # If not in cache, fetch from Zerodha
        logger.debug("Holdings not in cache, fetching from Zerodha")
        holdings = zerodha.get_holdings()
        
        # Store in cache
        logger.debug("Updating holdings cache")
        await redis.set(
            cache_key,
            holdings,
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

# Short Sell Scanner Endpoints

@app.get("/short-sell/alerts", status_code=status.HTTP_200_OK)
async def get_short_sell_alerts(
    scanner: ShortSellScanner = Depends(get_short_sell_scanner)
) -> Dict:
    """
    Get all active short sell alerts.
    
    Returns:
        Dict: List of active short sell opportunities
    """
    try:
        alerts = await scanner.get_active_alerts()
        return {
            "status": "success",
            "alerts": [alert.dict() for alert in alerts],
            "count": len(alerts)
        }
    except Exception as e:
        logger.error(f"Failed to get short sell alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alerts"
        )

@app.get("/short-sell/alerts/{instrument_token}", status_code=status.HTTP_200_OK)
async def get_short_sell_alert(
    instrument_token: str,
    scanner: ShortSellScanner = Depends(get_short_sell_scanner)
) -> Dict:
    """
    Get short sell alert for specific instrument.
    
    Args:
        instrument_token: Zerodha instrument token
        
    Returns:
        Dict: Alert details if active
    """
    try:
        alert = await scanner.get_alert_by_instrument(instrument_token)
        if alert:
            return {
                "status": "success",
                "alert": alert.dict()
            }
        else:
            return {
                "status": "not_found",
                "message": "No active alert for this instrument"
            }
    except Exception as e:
        logger.error(f"Failed to get alert for {instrument_token}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alert"
        )

@app.post("/short-sell/scan", status_code=status.HTTP_200_OK)
async def trigger_manual_scan(
    scanner: ShortSellScanner = Depends(get_short_sell_scanner)
) -> Dict:
    """
    Manually trigger a short sell scan.
    
    Returns:
        Dict: Scan results
    """
    try:
        await scanner._perform_scan()
        alerts = await scanner.get_active_alerts()
        return {
            "status": "success",
            "message": "Manual scan completed",
            "active_alerts": len(alerts)
        }
    except Exception as e:
        logger.error(f"Manual scan failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Manual scan failed"
        )