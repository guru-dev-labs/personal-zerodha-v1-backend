"""Test cases for Zerodha client"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from app.zerodha_client import ZerodhaClient

def test_zerodha_client_initialization():
    """Test ZerodhaClient initialization"""
    client = ZerodhaClient(api_key="test-key", api_secret="test-secret", redirect_url="http://localhost:8000/callback")
    assert client.api_key == "test-key"
    assert client.api_secret == "test-secret"
    assert client.redirect_url == "http://localhost:8000/callback"
    assert client._access_token is None

def test_get_login_url():
    """Test login URL generation"""
    client = ZerodhaClient(api_key="test-key", api_secret="test-secret", redirect_url="http://localhost:8000/callback")
    login_url = client.get_login_url()
    assert isinstance(login_url, str)
    assert "test-key" in login_url

@pytest.mark.asyncio
async def test_generate_session_success():
    """Test successful session generation"""
    client = ZerodhaClient(api_key="test-key", api_secret="test-secret", redirect_url="http://localhost:8000/callback")
    
    # Mock KiteConnect response
    mock_response = {
        "access_token": "test-access-token",
        "user_id": "TEST001"
    }
    client.kite.generate_session = Mock(return_value=mock_response)
    
    result = client.generate_session("test-request-token")
    assert result == mock_response
    assert client.access_token == "test-access-token"

@pytest.mark.asyncio
async def test_generate_session_failure():
    """Test session generation failure"""
    client = ZerodhaClient(api_key="test-key", api_secret="test-secret", redirect_url="http://localhost:8000/callback")
    
    # Mock failure
    client.kite.generate_session = Mock(side_effect=Exception("Auth failed"))
    
    with pytest.raises(HTTPException) as exc_info:
        client.generate_session("invalid-token")
    assert exc_info.value.status_code == 400
    assert "Failed to generate session" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_profile_success():
    """Test successful profile retrieval"""
    client = ZerodhaClient(api_key="test-key", api_secret="test-secret", redirect_url="http://localhost:8000/callback")
    
    # Mock profile data
    mock_profile = {
        "user_id": "TEST001",
        "user_name": "Test User",
        "email": "test@example.com"
    }
    client.kite.profile = Mock(return_value=mock_profile)
    
    result = client.get_profile()
    assert result == mock_profile

@pytest.mark.asyncio
async def test_get_profile_failure():
    """Test profile retrieval failure"""
    client = ZerodhaClient(api_key="test-key", api_secret="test-secret", redirect_url="http://localhost:8000/callback")
    
    # Mock failure
    client.kite.profile = Mock(side_effect=Exception("Failed to fetch profile"))
    
    with pytest.raises(HTTPException) as exc_info:
        client.get_profile()
    assert exc_info.value.status_code == 400
    assert "Failed to fetch profile" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_holdings_success():
    """Test successful holdings retrieval"""
    client = ZerodhaClient(api_key="test-key", api_secret="test-secret", redirect_url="http://localhost:8000/callback")
    
    # Mock holdings data
    mock_holdings = [{
        "tradingsymbol": "INFY",
        "exchange": "NSE",
        "quantity": 10,
        "average_price": 1500.0
    }]
    client.kite.holdings = Mock(return_value=mock_holdings)
    
    result = client.get_holdings()
    assert result == mock_holdings

@pytest.mark.asyncio
async def test_place_order_success():
    """Test successful order placement"""
    client = ZerodhaClient(api_key="test-key", api_secret="test-secret", redirect_url="http://localhost:8000/callback")
    
    # Mock order placement
    mock_order_id = "TEST_ORDER_001"
    client.kite.place_order = Mock(return_value=mock_order_id)
    
    result = client.place_order(
        tradingsymbol="INFY",
        exchange="NSE",
        transaction_type="BUY",
        quantity=1,
        product="CNC",
        order_type="MARKET"
    )
    assert result == mock_order_id

@pytest.mark.asyncio
async def test_place_order_with_price():
    """Test order placement with limit price"""
    client = ZerodhaClient(api_key="test-key", api_secret="test-secret", redirect_url="http://localhost:8000/callback")
    
    # Mock order placement
    mock_order_id = "TEST_ORDER_002"
    client.kite.place_order = Mock(return_value=mock_order_id)
    
    result = client.place_order(
        tradingsymbol="INFY",
        exchange="NSE",
        transaction_type="BUY",
        quantity=1,
        product="CNC",
        order_type="LIMIT",
        price=1500.0
    )
    assert result == mock_order_id
    # Verify price was included in the order
    client.kite.place_order.assert_called_once_with(
        tradingsymbol="INFY",
        exchange="NSE",
        transaction_type="BUY",
        quantity=1,
        product="CNC",
        order_type="LIMIT",
        price=1500.0
    )