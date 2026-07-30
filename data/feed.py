import logging
from datetime import datetime, timedelta, timezone
from typing import Protocol

import ccxt
import pandas as pd
import requests

from core.entities import Asset

logger = logging.getLogger(__name__)


class DataFeedProtocol(Protocol):
    def get_ohlcv(self, asset: Asset, timeframe: str, limit: int) -> pd.DataFrame: ...

    def get_fgi(self) -> int: ...

    def is_market_open(self, asset: Asset, max_delay_minutes: int) -> bool: ...


class LiveMarketDataFeed:
    def __init__(self, exchange: ccxt.Exchange) -> None:
        self._exchange = exchange

    def get_ohlcv(self, asset: Asset, timeframe: str = "1h", limit: int = 100) -> pd.DataFrame:
        try:
            ohlcv = self._exchange.fetch_ohlcv(asset.symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            return df
        except ccxt.BaseError as e:
            logger.error("Failed to fetch OHLCV for %s: %s", asset.symbol, e)
            raise

    def get_fgi(self) -> int:
        try:
            response = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
            response.raise_for_status()
            data = response.json()
            return int(data["data"][0]["value"])
        except (requests.RequestException, KeyError, ValueError) as e:
            logger.warning("Failed to fetch FGI Index, defaulting to 50 (Neutral): %s", e)
            return 50

    def is_market_open(self, asset: Asset, max_delay_minutes: int = 10) -> bool:
        try:
            ohlcv = self._exchange.fetch_ohlcv(asset.symbol, timeframe="1m", limit=2)
            if not ohlcv:
                return False

            last_timestamp = ohlcv[-1][0]
            last_candle = datetime.fromtimestamp(last_timestamp / 1000, tz=timezone.utc)
            now = datetime.now(timezone.utc)

            return (now - last_candle) <= timedelta(minutes=max_delay_minutes)
        except ccxt.BaseError as e:
            logger.warning("Market status check failed for %s: %s", asset.symbol, e)
            return False