import pandas as pd
import pandas_ta as ta
from strategy.indicators.base import IndicatorProtocol


class ATRIndicator:
    def __init__(self, period: int = 14, name: str = "atr") -> None:
        self._period = period
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def calculate(self, df: pd.DataFrame, context: dict | None = None) -> float:
        if df.empty or len(df) < self._period:
            return 0.0

        atr_series = df.ta.atr(length=self._period)
        if atr_series is None or atr_series.empty or pd.isna(atr_series.iloc[-1]):
            return 0.0

        return float(atr_series.iloc[-1])