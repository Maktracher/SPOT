from dataclasses import dataclass
import pandas as pd

from core.entities import Asset, SignalType, TradingSignal


@dataclass(frozen=True)
class StrategyConfig:
    rsi_period: int = 14
    atr_period: int = 14
    buy_threshold: float = 25.0
    sell_threshold: float = 70.0
    fgi_buy_max: int = 40
    fgi_sell_min: int = 60
    cancel_buy_threshold: float = 60.0
    cancel_sell_threshold: float = 40.0


class MultiAssetGridStrategy:
    def __init__(self, config: StrategyConfig = StrategyConfig()) -> None:
        self._config = config

    def calculate_rsi(self, df: pd.DataFrame) -> float:
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        roll_up = gain.ewm(alpha=1 / self._config.rsi_period, min_periods=self._config.rsi_period, adjust=False).mean()
        roll_down = loss.ewm(alpha=1 / self._config.rsi_period, min_periods=self._config.rsi_period, adjust=False).mean()

        rs = roll_up / roll_down
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return float(rsi.iloc[-1])

    def calculate_atr(self, df: pd.DataFrame) -> float:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=self._config.atr_period).mean().iloc[-1]
        return float(atr)

    def analyze(self, asset: Asset, ohlcv_df: pd.DataFrame, fgi: int) -> TradingSignal:
        rsi = self.calculate_rsi(ohlcv_df)
        atr = self.calculate_atr(ohlcv_df)
        current_price = float(ohlcv_df["close"].iloc[-1])

        signal_type = SignalType.HOLD

        if rsi <= self._config.buy_threshold and fgi <= self._config.fgi_buy_max:
            signal_type = SignalType.BUY
        elif rsi >= self._config.sell_threshold and fgi >= self._config.fgi_sell_min:
            signal_type = SignalType.SELL
        elif rsi >= self._config.cancel_buy_threshold:
            signal_type = SignalType.CANCEL_BUY
        elif rsi <= self._config.cancel_sell_threshold:
            signal_type = SignalType.CANCEL_SELL

        return TradingSignal(
            asset=asset,
            signal_type=signal_type,
            rsi=round(rsi, 2),
            fgi=fgi,
            current_price=current_price,
            atr=atr,
        )