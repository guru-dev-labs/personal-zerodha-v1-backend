"""
Screener Module

This module handles all market screening functionality, including:
1. Technical analysis calculations
2. Condition evaluation
3. Real-time screening
4. Alert generation
5. Backtesting support
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import talib
from fastapi import HTTPException, status

from .models import (
    Screener, ScreenerCondition, TimeFrame, 
    ConditionOperator, Alert, AlertType
)
from .zerodha_client import ZerodhaClient

logger = logging.getLogger(__name__)

class ScreenerEngine:
    """
    Engine for processing market screeners and generating alerts.
    Handles technical analysis, condition evaluation, and alert generation.
    """
    
    def __init__(self, zerodha_client: ZerodhaClient):
        """
        Initialize screener engine with dependencies
        
        Args:
            zerodha_client: Authenticated Zerodha client instance
        """
        self.zerodha = zerodha_client
        self.indicators = {
            'sma': self._calculate_sma,
            'ema': self._calculate_ema,
            'rsi': self._calculate_rsi,
            'macd': self._calculate_macd,
            'bollinger_bands': self._calculate_bollinger_bands,
            'atr': self._calculate_atr,
            'volume_sma': self._calculate_volume_sma
        }

    async def process_screener(
        self,
        screener: Screener,
        instruments: List[str]
    ) -> Dict[str, Any]:
        """
        Process a screener against given instruments
        
        Args:
            screener: Screener configuration
            instruments: List of instrument tokens to screen
            
        Returns:
            Dict containing matching instruments and their data
        """
        try:
            logger.info(f"Processing screener {screener.id} for {len(instruments)} instruments")
            results = {}
            
            for instrument in instruments:
                # Get historical data
                data = await self._get_historical_data(
                    instrument,
                    screener.time_frame,
                    max_lookback_period=self._get_max_lookback(screener.conditions)
                )
                
                # Calculate indicators and evaluate conditions
                if await self._evaluate_conditions(data, screener.conditions):
                    results[instrument] = {
                        'timestamp': datetime.utcnow(),
                        'data': data.iloc[-1].to_dict(),
                        'matched_conditions': [str(c) for c in screener.conditions]
                    }
            
            logger.info(f"Screener {screener.id} found {len(results)} matches")
            return results
            
        except Exception as e:
            logger.error(f"Error processing screener: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Screener processing failed: {str(e)}"
            )

    async def _get_historical_data(
        self,
        instrument: str,
        time_frame: TimeFrame,
        max_lookback_period: int
    ) -> pd.DataFrame:
        """
        Get historical market data for analysis
        
        Args:
            instrument: Instrument token
            time_frame: Time frame for data
            max_lookback_period: Maximum lookback needed for indicators
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Convert timeframe to Zerodha format
            interval_map = {
                TimeFrame.ONE_MINUTE: "minute",
                TimeFrame.FIVE_MINUTES: "5minute",
                TimeFrame.FIFTEEN_MINUTES: "15minute",
                TimeFrame.THIRTY_MINUTES: "30minute",
                TimeFrame.ONE_HOUR: "60minute",
                TimeFrame.ONE_DAY: "day"
            }
            
            # Calculate from_date based on lookback
            from_date = datetime.now() - timedelta(days=max_lookback_period + 1)
            
            # Fetch historical data
            data = self.zerodha.kite.historical_data(
                instrument_token=instrument,
                from_date=from_date,
                to_date=datetime.now(),
                interval=interval_map[time_frame]
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df.set_index('date', inplace=True)
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            raise

    def _get_max_lookback(self, conditions: List[ScreenerCondition]) -> int:
        """Calculate maximum lookback period needed for all conditions"""
        max_period = 0
        for condition in conditions:
            if condition.lookback_period:
                max_period = max(max_period, condition.lookback_period)
        return max(max_period, 100)  # Minimum 100 periods for reliable signals

    async def _evaluate_conditions(
        self,
        data: pd.DataFrame,
        conditions: List[ScreenerCondition]
    ) -> bool:
        """
        Evaluate all conditions for a screener
        
        Args:
            data: Historical market data
            conditions: List of conditions to evaluate
            
        Returns:
            bool: True if all conditions are met
        """
        try:
            for condition in conditions:
                # Calculate indicator value
                if condition.indicator in self.indicators:
                    indicator_value = await self.indicators[condition.indicator](
                        data,
                        condition.lookback_period
                    )
                else:
                    indicator_value = data[condition.indicator]

                # Get latest value
                current_value = indicator_value.iloc[-1]

                # Evaluate condition
                if not self._evaluate_single_condition(
                    current_value,
                    condition.operator,
                    condition.value,
                    indicator_value if condition.operator in ['crosses_above', 'crosses_below'] else None
                ):
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating conditions: {str(e)}")
            return False

    def _evaluate_single_condition(
        self,
        current_value: float,
        operator: ConditionOperator,
        target_value: float,
        historical_values: Optional[pd.Series] = None
    ) -> bool:
        """
        Evaluate a single screening condition
        
        Args:
            current_value: Current indicator value
            operator: Condition operator
            target_value: Target value to compare against
            historical_values: Historical values for crossover conditions
            
        Returns:
            bool: True if condition is met
        """
        try:
            if operator == ConditionOperator.GREATER_THAN:
                return current_value > target_value
            elif operator == ConditionOperator.LESS_THAN:
                return current_value < target_value
            elif operator == ConditionOperator.EQUAL_TO:
                return abs(current_value - target_value) < 0.0001
            elif operator == ConditionOperator.GREATER_EQUAL:
                return current_value >= target_value
            elif operator == ConditionOperator.LESS_EQUAL:
                return current_value <= target_value
            elif operator == ConditionOperator.CROSSES_ABOVE:
                if historical_values is None or len(historical_values) < 2:
                    return False
                return (
                    historical_values.iloc[-2] <= target_value and
                    historical_values.iloc[-1] > target_value
                )
            elif operator == ConditionOperator.CROSSES_BELOW:
                if historical_values is None or len(historical_values) < 2:
                    return False
                return (
                    historical_values.iloc[-2] >= target_value and
                    historical_values.iloc[-1] < target_value
                )
            elif operator == ConditionOperator.PERCENT_CHANGE:
                if historical_values is None or len(historical_values) < 2:
                    return False
                change = (
                    (historical_values.iloc[-1] - historical_values.iloc[-2]) /
                    historical_values.iloc[-2] * 100
                )
                return abs(change) >= target_value
                
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating condition: {str(e)}")
            return False

    # Technical Indicator Calculations
    async def _calculate_sma(
        self,
        data: pd.DataFrame,
        period: int = 20
    ) -> pd.Series:
        """Calculate Simple Moving Average"""
        return talib.SMA(data['close'], timeperiod=period)

    async def _calculate_ema(
        self,
        data: pd.DataFrame,
        period: int = 20
    ) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return talib.EMA(data['close'], timeperiod=period)

    async def _calculate_rsi(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """Calculate Relative Strength Index"""
        return talib.RSI(data['close'], timeperiod=period)

    async def _calculate_macd(
        self,
        data: pd.DataFrame,
        period: int = None  # Not used, MACD uses standard periods
    ) -> pd.Series:
        """Calculate MACD"""
        macd, signal, hist = talib.MACD(
            data['close'],
            fastperiod=12,
            slowperiod=26,
            signalperiod=9
        )
        return macd

    async def _calculate_bollinger_bands(
        self,
        data: pd.DataFrame,
        period: int = 20
    ) -> pd.Series:
        """Calculate Bollinger Bands"""
        upper, middle, lower = talib.BBANDS(
            data['close'],
            timeperiod=period,
            nbdevup=2,
            nbdevdn=2,
            matype=0
        )
        return middle  # Return middle band for comparisons

    async def _calculate_atr(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """Calculate Average True Range"""
        return talib.ATR(
            data['high'],
            data['low'],
            data['close'],
            timeperiod=period
        )

    async def _calculate_volume_sma(
        self,
        data: pd.DataFrame,
        period: int = 20
    ) -> pd.Series:
        """Calculate Volume Simple Moving Average"""
        return talib.SMA(data['volume'], timeperiod=period)
