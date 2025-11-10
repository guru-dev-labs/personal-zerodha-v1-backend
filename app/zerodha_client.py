"""
Zerodha Client Module

This module provides a client interface for interacting with Zerodha's Kite Connect APIs.
It handles authentication, session management, and trading operations with proper error
handling and logging.

Typical usage:
    client = ZerodhaClient(api_key="your_key", api_secret="your_secret")
    login_url = client.get_login_url()
    # After user logs in and you get request_token
    session = client.generate_session(request_token)
"""

from typing import Dict, Optional, List
import logging
import logging.handlers
import sys
import requests
from kiteconnect import KiteConnect
from fastapi import HTTPException

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.handlers.RotatingFileHandler(
    'zerodha_client.log',
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

class ZerodhaClient:
    """
    A client for interacting with Zerodha's Kite Connect APIs.
    Handles authentication, session management, and API operations.
    """
    def __init__(self, api_key: str, api_secret: str, redirect_url: Optional[str] = None):
        """
        Initialize the Zerodha client with API credentials and redirect URL
        
        Args:
            api_key: The API key from Zerodha
            api_secret: The API secret from Zerodha
            redirect_url: The OAuth redirect URL (from config). Optional to allow
                creating a client instance in contexts where redirect URL is not
                required (e.g., background tasks or tests).
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_url = redirect_url
        self.kite = KiteConnect(api_key=api_key)
        self._access_token = None

    @property
    def access_token(self) -> Optional[str]:
        """Get the current access token"""
        return self._access_token

    def set_access_token(self, access_token: str) -> None:
        """
        Set the access token and initialize the Kite instance
        
        Args:
            access_token: The access token from Zerodha authentication
        """
        self._access_token = access_token
        self.kite.set_access_token(access_token)

    def get_login_url(self) -> str:
        """
        Get the Zerodha login URL for user authentication
        Returns:
            str: The login URL
        """
        return self.kite.login_url()

    def generate_session(self, request_token: str) -> Dict:
        """
        Generate a new session using the request token
        
        Args:
            request_token: The request token received after user authentication
            
        Returns:
            Dict: Session details including access token
            
        Raises:
            HTTPException: If session generation fails
        """
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.set_access_token(data["access_token"])
            return data
        except Exception as e:
            # Log full traceback and include exception text to help debugging
            logger.error(f"Failed to generate session: %s", str(e), exc_info=True)
            raise HTTPException(status_code=400, detail=f"Failed to generate session: {str(e)}")

    def get_profile(self) -> Dict:
        """
        Get user profile information
        
        Returns:
            Dict: User profile data
            
        Raises:
            HTTPException: If profile fetch fails
        """
        try:
            return self.kite.profile()
        except Exception as e:
            # Log full traceback and include exception text to help debugging
            logger.error(f"Failed to fetch profile: %s", str(e), exc_info=True)
            raise HTTPException(status_code=400, detail=f"Failed to fetch profile: {str(e)}")

    def get_positions(self) -> Dict:
        """
        Get user's current positions
        
        Returns:
            Dict: Position information
            
        Raises:
            HTTPException: If position fetch fails
        """
        try:
            return self.kite.positions()
        except Exception as e:
            logger.error(f"Failed to fetch positions: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to fetch positions")

    def get_holdings(self) -> Dict:
        """
        Get user's holdings
        
        Returns:
            Dict: Holdings information
            
        Raises:
            HTTPException: If holdings fetch fails
        """
        try:
            return self.kite.holdings()
        except Exception as e:
            logger.error(f"Failed to fetch holdings: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to fetch holdings")

    def place_order(self, 
                   tradingsymbol: str,
                   exchange: str,
                   transaction_type: str,
                   quantity: int,
                   product: str,
                   order_type: str,
                   price: Optional[float] = None,
                   trigger_price: Optional[float] = None) -> str:
        """
        Place a new order
        
        Args:
            tradingsymbol: Symbol of the instrument
            exchange: Exchange (NSE, BSE, etc.)
            transaction_type: BUY or SELL
            quantity: Number of shares/units
            product: Product code (CNC, MIS, etc.)
            order_type: Order type (MARKET, LIMIT, etc.)
            price: Order price (for LIMIT orders)
            trigger_price: Trigger price (for SL orders)
            
        Returns:
            str: Order ID
            
        Raises:
            HTTPException: If order placement fails
        """
        try:
            order_args = {
                "tradingsymbol": tradingsymbol,
                "exchange": exchange,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "product": product,
                "order_type": order_type
            }
            
            if price:
                order_args["price"] = price
            if trigger_price:
                order_args["trigger_price"] = trigger_price

            order_id = self.kite.place_order(**order_args)
            return order_id
        except Exception as e:
            logger.error(f"Failed to place order: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to place order")