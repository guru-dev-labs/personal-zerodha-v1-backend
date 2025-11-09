"""Test configuration and fixtures"""

import os
import pytest
import pandas as pd
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import logging

# Configure test logging
logging.basicConfig(level=logging.DEBUG)

# Import our FastAPI app and dependencies
from app.main import app
from app.config import get_settings, Settings
from app.zerodha_client import ZerodhaClient
from app.database import get_redis, init_redis_pool

# Create test settings
@pytest.fixture
def test_settings():
    """Provide test settings"""
    return Settings(
        SUPABASE_URL="http://test.supabase.co",
        SUPABASE_KEY="test-key",
        KITE_API_KEY="test-kite-api-key",
        KITE_API_SECRET="test-kite-secret",
        REDIS_HOST="localhost",
        REDIS_PORT=6379,
        DEBUG=True
    )

# Create a test client
@pytest.fixture
def test_client():
    """Create a test client for our FastAPI app"""
    return TestClient(app)

# Mock Zerodha client
@pytest.fixture
def mock_zerodha_client(mocker):
    """Provide a mocked Zerodha client"""
    mock_client = mocker.patch('app.zerodha_client.ZerodhaClient')
    mock_client.get_login_url.return_value = "http://test-login-url"
    mock_client.get_profile.return_value = {
        "user_id": "TEST001",
        "user_name": "Test User",
        "email": "test@example.com"
    }
    return mock_client

# Mock Redis
@pytest.fixture
async def mock_redis(mocker):
    """Provide a mocked Redis client"""
    mock_redis = mocker.patch('app.database.get_redis')
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    return mock_redis

@pytest.fixture
def sample_historical_data():
    """Create sample market data for testing"""
    dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'open': [100 + i * 0.1 for i in range(100)],
        'high': [101 + i * 0.1 for i in range(100)],
        'low': [99 + i * 0.1 for i in range(100)],
        'close': [100.5 + i * 0.1 for i in range(100)],
        'volume': [1000000 + i * 1000 for i in range(100)]
    }, index=dates)
    return data

@pytest.fixture
def sample_screener():
    """Create a sample screener for testing"""
    from app.models import Screener, ScreenerCondition, TimeFrame, ConditionOperator
    return Screener(
        id="test-screener-id",
        name="Test Screener",
        description="A test screener",
        user_id="test-user-id",
        time_frame=TimeFrame.ONE_DAY,
        conditions=[
            ScreenerCondition(
                indicator="rsi",
                operator=ConditionOperator.LESS_THAN,
                value=30,
                lookback_period=14
            ),
            ScreenerCondition(
                indicator="sma",
                operator=ConditionOperator.CROSSES_ABOVE,
                value=200,
                lookback_period=200
            )
        ],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )