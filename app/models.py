from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

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

class MarketData(BaseModel):
    id: UUID
    instrument_token: str
    data: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
