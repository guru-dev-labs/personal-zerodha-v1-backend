"""
Database Models Module

This module defines all the Pydantic models used for data validation and 
database schema representation in the application. It includes models for:
- User management
- Market data
- Screeners and conditions
- Trading strategies
- Alerts and notifications
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator

class UserBase(BaseModel):
    zerodha_user_id: str
    zerodha_api_key: str
    is_active: bool = True

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    zerodha_access_token: Optional[str] = None
    zerodha_refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    zerodha_access_token: Optional[str] = None
    zerodha_refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TimeFrame(str, Enum):
    """Time frame options for screener and alerts"""
    ONE_MINUTE = "1minute"
    FIVE_MINUTES = "5minute"
    FIFTEEN_MINUTES = "15minute"
    THIRTY_MINUTES = "30minute"
    ONE_HOUR = "1hour"
    ONE_DAY = "1day"

class ConditionOperator(str, Enum):
    """Available operators for screener conditions"""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    EQUAL_TO = "="
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"
    PERCENT_CHANGE = "percent_change"

class ScreenerCondition(BaseModel):
    """Individual condition for a screener"""
    id: Optional[UUID] = None
    indicator: str = Field(..., description="Technical indicator or price data point")
    operator: ConditionOperator
    value: float
    lookback_period: Optional[int] = Field(default=None, description="Period for indicators like MA")
    
    @validator('indicator')
    def validate_indicator(cls, v):
        valid_indicators = {
            'close', 'open', 'high', 'low', 'volume',
            'sma', 'ema', 'rsi', 'macd', 'bollinger_bands',
            'atr', 'volume_sma'
        }
        if v.lower() not in valid_indicators:
            raise ValueError(f"Invalid indicator. Must be one of: {valid_indicators}")
        return v.lower()

class ScreenerCreate(BaseModel):
    """Create a new screener"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    time_frame: TimeFrame
    conditions: List[ScreenerCondition]
    is_active: bool = True
    notification_enabled: bool = True

class Screener(ScreenerCreate):
    """Complete screener model with system fields"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    last_alert_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AlertType(str, Enum):
    """Types of alerts that can be generated"""
    PRICE = "price"
    INDICATOR = "indicator"
    SCREENER = "screener"
    VOLUME = "volume"
    CUSTOM = "custom"

class AlertCreate(BaseModel):
    """Create a new alert"""
    instrument_token: str
    type: AlertType
    condition: ScreenerCondition
    message_template: str = Field(..., max_length=500)
    is_active: bool = True
    time_frame: TimeFrame

class Alert(AlertCreate):
    """Complete alert model with system fields"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0

    class Config:
        from_attributes = True

class MarketData(BaseModel):
    """Market data storage model"""
    id: UUID
    instrument_token: str
    time_frame: TimeFrame
    data: Dict[str, Any] = Field(..., description="OHLCV and indicator data")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BacktestResult(BaseModel):
    """Store backtesting results"""
    id: UUID
    screener_id: UUID
    start_date: datetime
    end_date: datetime
    instruments: List[str]
    results: Dict[str, Any]
    metrics: Dict[str, float]
    created_at: datetime

    class Config:
        from_attributes = True

class ShortSellAlert(BaseModel):
    """Short sell opportunity alert"""
    id: UUID
    instrument_token: str
    instrument_name: str
    current_price: float
    price_change_5min: float  # Percentage change in last 5 minutes
    distance_from_upper_circuit: float  # Percentage away from upper circuit
    weekly_movement: float  # Movement in last week
    created_at: datetime
    expires_at: datetime  # 5 minutes from creation
    is_active: bool = True

    class Config:
        from_attributes = True

class ShortSellAlertCreate(BaseModel):
    """Create a short sell alert"""
    instrument_token: str
    instrument_name: str
    current_price: float
    price_change_5min: float
    distance_from_upper_circuit: float
    weekly_movement: float
