"""Test cases for market screener functionality"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

from app.screener import ScreenerEngine
from app.models import (
    Screener, ScreenerCondition, TimeFrame, 
    ConditionOperator, Alert, AlertType
)

@pytest.fixture
def sample_historical_data():
    """Create sample market data for testing"""
    dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'timestamp': dates,  # Use 'timestamp' column for Zerodha compatibility
        'open': [100 + i * 0.1 for i in range(100)],
        'high': [101 + i * 0.1 for i in range(100)],
        'low': [99 + i * 0.1 for i in range(100)],
        'close': [100.5 + i * 0.1 for i in range(100)],
        'volume': [1000000 + i * 1000 for i in range(100)]
    })
    return data

@pytest.fixture
def mock_zerodha_client():
    """Create a mock Zerodha client"""
    mock_client = Mock()
    mock_client.kite = Mock()
    return mock_client

@pytest.fixture
def screener_engine(mock_zerodha_client):
    """Create a screener engine instance"""
    return ScreenerEngine(mock_zerodha_client)

def test_screener_initialization(screener_engine):
    """Test screener engine initialization"""
    assert screener_engine.zerodha is not None
    assert len(screener_engine.indicators) > 0

@pytest.mark.asyncio
async def test_calculate_sma(screener_engine, sample_historical_data):
    """Test SMA calculation"""
    period = 20
    sma = await screener_engine._calculate_sma(sample_historical_data, period)
    assert len(sma) == len(sample_historical_data)
    assert pd.isna(sma[:period-1]).all()  # First (period-1) values should be NaN
    assert not pd.isna(sma[period:]).any()  # Rest should be calculated

@pytest.mark.asyncio
async def test_calculate_rsi(screener_engine, sample_historical_data):
    """Test RSI calculation"""
    rsi = await screener_engine._calculate_rsi(sample_historical_data)
    assert len(rsi) == len(sample_historical_data)
    assert all(0 <= x <= 100 for x in rsi.dropna())  # RSI should be between 0 and 100

def test_evaluate_single_condition(screener_engine):
    """Test condition evaluation"""
    # Test greater than
    assert screener_engine._evaluate_single_condition(10, ConditionOperator.GREATER_THAN, 5)
    assert not screener_engine._evaluate_single_condition(5, ConditionOperator.GREATER_THAN, 10)
    
    # Test crosses above
    series = pd.Series([9, 11])  # Previous value = 9, current value = 11
    assert screener_engine._evaluate_single_condition(11, ConditionOperator.CROSSES_ABOVE, 10, series)
    assert not screener_engine._evaluate_single_condition(11, ConditionOperator.CROSSES_ABOVE, 12, series)

@pytest.mark.asyncio
async def test_process_screener(screener_engine, sample_historical_data, mock_zerodha_client):
    """Test complete screener processing"""
    # Mock historical data retrieval
    mock_zerodha_client.kite.historical_data.return_value = sample_historical_data.reset_index().to_dict('records')
    
    # Create test screener
    screener = Screener(
        id=str(uuid4()),
        name="Test Screener",
        description="Test screener with RSI condition",
        user_id=str(uuid4()),
        time_frame=TimeFrame.ONE_DAY,
        conditions=[
            ScreenerCondition(
                indicator="rsi",
                operator=ConditionOperator.LESS_THAN,
                value=30,
                lookback_period=14
            )
        ],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Process screener
    results = await screener_engine.process_screener(screener, ["TEST"])
    
    # Verify results structure
    assert isinstance(results, dict)
    for token, data in results.items():
        assert "timestamp" in data
        assert "data" in data
        assert "matched_conditions" in data

@pytest.mark.asyncio
async def test_get_historical_data(screener_engine, sample_historical_data, mock_zerodha_client):
    """Test historical data retrieval"""
    # Mock the Kite response
    mock_zerodha_client.kite.historical_data.return_value = sample_historical_data.reset_index().to_dict('records')
    
    data = await screener_engine._get_historical_data(
        "TEST",
        TimeFrame.ONE_DAY,
        100
    )
    
    assert isinstance(data, pd.DataFrame)
    assert len(data) > 0
    assert all(col in data.columns for col in ['open', 'high', 'low', 'close', 'volume'])

@pytest.mark.asyncio
async def test_evaluate_conditions(screener_engine, sample_historical_data):
    """Test condition evaluation"""
    conditions = [
        ScreenerCondition(
            indicator="close",
            operator=ConditionOperator.GREATER_THAN,
            value=100
        ),
        ScreenerCondition(
            indicator="volume",
            operator=ConditionOperator.GREATER_THAN,
            value=1000000
        )
    ]
    
    result = await screener_engine._evaluate_conditions(sample_historical_data, conditions)
    assert isinstance(result, bool)

def test_get_max_lookback(screener_engine):
    """Test lookback period calculation"""
    conditions = [
        ScreenerCondition(
            indicator="sma",
            operator=ConditionOperator.GREATER_THAN,
            value=100,
            lookback_period=20
        ),
        ScreenerCondition(
            indicator="rsi",
            operator=ConditionOperator.LESS_THAN,
            value=30,
            lookback_period=14
        )
    ]
    
    max_lookback = screener_engine._get_max_lookback(conditions)
    assert max_lookback >= 100  # Should be at least 100 for reliable signals
    assert max_lookback >= max(c.lookback_period for c in conditions if c.lookback_period)