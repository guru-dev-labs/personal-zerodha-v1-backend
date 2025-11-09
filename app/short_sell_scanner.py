"""
Short Sell Scanner Module

This module implements a continuous scanner for short selling opportunities
based on specific market conditions for Nifty 500 stocks.
"""

import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional
import pandas as pd
from fastapi import HTTPException, status

from .models import ShortSellAlert, ShortSellAlertCreate
from .zerodha_client import ZerodhaClient
from .database import Database

logger = logging.getLogger(__name__)

class ShortSellScanner:
    """
    Scanner for identifying short selling opportunities based on:
    - 4%+ price increase in last 5 minutes
    - At least 10% away from upper circuit
    - Price between 150-900
    - Weekly movement ≤5%
    - Market hours: 9:25 AM - 3:00 PM
    """

    def __init__(self, zerodha_client: ZerodhaClient):
        self.zerodha = zerodha_client
        self.redis = None
        self.nifty_500_instruments = []  # Will be populated
        self.scan_interval = 60  # Scan every 60 seconds
        self.alert_lifetime = 300  # 5 minutes in seconds
        self.api_call_count = 0
        self.api_call_reset_time = datetime.now()
        self.max_api_calls_per_minute = 1000  # Zerodha limit

    async def initialize(self):
        """Initialize scanner with Nifty 500 instruments"""
        self.redis = await Database.get_redis()
        await self._load_nifty_500_instruments()
        logger.info(f"Initialized scanner with {len(self.nifty_500_instruments)} instruments")

    async def _load_nifty_500_instruments(self):
        """Load Nifty 500 instrument list"""
        try:
            # Get all instruments
            instruments = self.zerodha.kite.instruments()

            # Filter for Nifty 500 stocks (NSE equity)
            nifty_500 = [
                inst for inst in instruments
                if inst['exchange'] == 'NSE' and
                inst['segment'] == 'NSE' and
                inst['instrument_type'] == 'EQ' and
                inst.get('nse_code', '').strip()  # Has NSE code
            ]

            self.nifty_500_instruments = [str(inst['instrument_token']) for inst in nifty_500[:500]]  # Limit to 500
            logger.info(f"Loaded {len(self.nifty_500_instruments)} Nifty 500 instruments")

        except Exception as e:
            logger.error(f"Error loading Nifty 500 instruments: {str(e)}")
            # Fallback to some known instruments
            self.nifty_500_instruments = [
                '738561',  # RELIANCE
                '1270529', # TCS
                '2953217', # HDFC
                '134657',  # INFY
                '2714625', # ICICIBANK
            ]

    async def start_continuous_scanning(self):
        """Start continuous scanning loop"""
        logger.info("Starting continuous short sell scanning...")

        while True:
            try:
                # Check if market is open
                if not self._is_market_open():
                    logger.info("Market closed, sleeping for 5 minutes...")
                    await asyncio.sleep(300)
                    continue

                # Perform scan
                await self._perform_scan()

                # Wait for next scan
                await asyncio.sleep(self.scan_interval)

            except Exception as e:
                logger.error(f"Error in scanning loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retry

    def _is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        market_start = time(9, 25)  # 9:25 AM
        market_end = time(15, 0)    # 3:00 PM

        return (
            now.weekday() < 5 and  # Monday to Friday
            market_start <= now.time() <= market_end
        )

    async def _perform_scan(self):
        """Perform one complete scan of all instruments"""
        logger.info(f"Starting scan of {len(self.nifty_500_instruments)} instruments")

        active_alerts = 0

        for instrument_token in self.nifty_500_instruments:
            try:
                # Check if this instrument qualifies
                alert_data = await self._check_instrument(instrument_token)
                if alert_data:
                    await self._create_alert(alert_data)
                    active_alerts += 1

                # Rate limiting - small delay between instruments
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error checking instrument {instrument_token}: {str(e)}")
                continue

        logger.info(f"Scan complete. Found {active_alerts} new alerts")

    async def _check_instrument(self, instrument_token: str) -> Optional[Dict[str, Any]]:
        """Check if instrument meets short sell criteria"""
        try:
            # Rate limiting check
            if not await self._check_rate_limit():
                logger.warning("API rate limit reached, skipping instrument check")
                return None

            # Try to get from cache first (5-minute cache)
            cache_key = f"instrument_data:{instrument_token}"
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                # Use cached data
                data_5min = eval(cached_data)  # In production, use proper JSON
            else:
                # Get 5-minute data for last 5 minutes
                from_date = datetime.now() - timedelta(minutes=10)
                data_5min = self.zerodha.kite.historical_data(
                    instrument_token=instrument_token,
                    from_date=from_date,
                    to_date=datetime.now(),
                    interval="5minute"
                )
                self.api_call_count += 1
                
                # Cache for 5 minutes
                await self.redis.set(cache_key, str(data_5min), ex=300)

            if len(data_5min) < 2:
                return None

            # Get daily data for last week (cached separately)
            cache_key_daily = f"instrument_daily:{instrument_token}"
            cached_daily = await self.redis.get(cache_key_daily)
            
            if cached_daily:
                data_daily = eval(cached_daily)
            else:
                from_date_week = datetime.now() - timedelta(days=8)
                data_daily = self.zerodha.kite.historical_data(
                    instrument_token=instrument_token,
                    from_date=from_date_week,
                    to_date=datetime.now(),
                    interval="day"
                )
                self.api_call_count += 1
                
                # Cache daily data for 1 hour
                await self.redis.set(cache_key_daily, str(data_daily), ex=3600)

            # Convert to DataFrame
            df_5min = pd.DataFrame(data_5min)
            df_daily = pd.DataFrame(data_daily)

            if df_5min.empty or df_daily.empty:
                return None

            # Get current price and instrument info
            current_price = df_5min['close'].iloc[-1]

            # Check price range (150-900)
            if not (150 <= current_price <= 900):
                return None

            # Check 5-minute price change >= 4%
            price_5min_ago = df_5min['close'].iloc[-2]
            price_change_5min = ((current_price - price_5min_ago) / price_5min_ago) * 100
            if price_change_5min < 4:
                return None

            # Check distance from upper circuit (>=10%)
            # Note: Zerodha doesn't provide circuit limits directly
            # We'll use a proxy: check if price is not too close to recent high
            recent_high = df_5min['high'].max()
            distance_from_high = ((recent_high - current_price) / current_price) * 100
            if distance_from_high < 10:
                return None

            # Check weekly movement <=5%
            if len(df_daily) >= 2:
                week_start_price = df_daily['close'].iloc[0]
                week_end_price = df_daily['close'].iloc[-1]
                weekly_movement = abs((week_end_price - week_start_price) / week_start_price) * 100
                if weekly_movement > 5:
                    return None

            # Get instrument name (cached)
            cache_key_name = f"instrument_name:{instrument_token}"
            instrument_name = await self.redis.get(cache_key_name)
            
            if not instrument_name:
                instrument_info = self.zerodha.kite.instruments(instrument_token=instrument_token)
                instrument_name = instrument_info[0]['tradingsymbol'] if instrument_info else "Unknown"
                await self.redis.set(cache_key_name, instrument_name, ex=86400)  # Cache for 1 day
                self.api_call_count += 1
            else:
                instrument_name = instrument_name.decode('utf-8')

            return {
                'instrument_token': instrument_token,
                'instrument_name': instrument_name,
                'current_price': current_price,
                'price_change_5min': price_change_5min,
                'distance_from_upper_circuit': distance_from_high,
                'weekly_movement': weekly_movement
            }

        except Exception as e:
            logger.error(f"Error checking instrument {instrument_token}: {str(e)}")
            return None

    async def _check_rate_limit(self) -> bool:
        """Check if we're within API rate limits"""
        now = datetime.now()
        
        # Reset counter every minute
        if (now - self.api_call_reset_time).seconds >= 60:
            self.api_call_count = 0
            self.api_call_reset_time = now
        
        return self.api_call_count < self.max_api_calls_per_minute

    async def _create_alert(self, alert_data: Dict[str, Any]):
        """Create and store a short sell alert"""
        try:
            alert = ShortSellAlertCreate(**alert_data)

            # Store in Redis with expiration
            alert_key = f"short_sell_alert:{alert.instrument_token}"
            alert_data_dict = {
                'id': str(alert.instrument_token),  # Use token as ID for simplicity
                'instrument_token': alert.instrument_token,
                'instrument_name': alert.instrument_name,
                'current_price': alert.current_price,
                'price_change_5min': alert.price_change_5min,
                'distance_from_upper_circuit': alert.distance_from_upper_circuit,
                'weekly_movement': alert.weekly_movement,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=self.alert_lifetime)).isoformat(),
                'is_active': True
            }

            await self.redis.hset(alert_key, mapping=alert_data_dict)
            await self.redis.expire(alert_key, self.alert_lifetime)

            logger.info(f"Created short sell alert for {alert.instrument_name}")

            # TODO: Send notification
            await self._send_notification(alert)

        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")

    async def _send_notification(self, alert: ShortSellAlertCreate):
        """Send notification for new alert"""
        # TODO: Implement proper notification system (email, SMS, push)
        message = (
            f"🚨 SHORT SELL OPPORTUNITY 🚨\n"
            f"Stock: {alert.instrument_name}\n"
            f"Price: ₹{alert.current_price:.2f}\n"
            f"5-min Change: +{alert.price_change_5min:.2f}%\n"
            f"Distance from Circuit: {alert.distance_from_upper_circuit:.2f}%\n"
            f"Weekly Movement: {alert.weekly_movement:.2f}%\n"
            f"Valid for 5 minutes!"
        )
        
        logger.warning(message)
        
        # For now, just log. In production, integrate with:
        # - Email service (SendGrid, AWS SES)
        # - SMS service (Twilio, AWS SNS)  
        # - Push notifications (Firebase, etc.)

    async def get_active_alerts(self) -> List[ShortSellAlert]:
        """Get all active short sell alerts"""
        try:
            alerts = []
            keys = await self.redis.keys("short_sell_alert:*")

            for key in keys:
                alert_data = await self.redis.hgetall(key)
                if alert_data and alert_data.get('is_active') == 'True':
                    # Convert string dates back to datetime
                    alert_data['created_at'] = datetime.fromisoformat(alert_data['created_at'])
                    alert_data['expires_at'] = datetime.fromisoformat(alert_data['expires_at'])

                    # Convert numeric fields
                    for field in ['current_price', 'price_change_5min', 'distance_from_upper_circuit', 'weekly_movement']:
                        alert_data[field] = float(alert_data[field])

                    alerts.append(ShortSellAlert(**alert_data))

            return alerts

        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            return []

    async def get_alert_by_instrument(self, instrument_token: str) -> Optional[ShortSellAlert]:
        """Get active alert for specific instrument"""
        try:
            alert_key = f"short_sell_alert:{instrument_token}"
            alert_data = await self.redis.hgetall(alert_key)

            if alert_data and alert_data.get('is_active') == 'True':
                alert_data['created_at'] = datetime.fromisoformat(alert_data['created_at'])
                alert_data['expires_at'] = datetime.fromisoformat(alert_data['expires_at'])

                for field in ['current_price', 'price_change_5min', 'distance_from_upper_circuit', 'weekly_movement']:
                    alert_data[field] = float(alert_data[field])

                return ShortSellAlert(**alert_data)

            return None

        except Exception as e:
            logger.error(f"Error getting alert for {instrument_token}: {str(e)}")
            return None