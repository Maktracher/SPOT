import pandas as pd
import pandas_ta as ta
from strategy.indicators.base import IndicatorProtocol


class RSIIndicator:
    def __init__(self, period: int = 14, name: str = "rsi") -> None:
        self._period = period
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def calculate(self, df: pd.DataFrame, context: dict | None = None) -> float:
        if df.empty or len(df) < self._period:
            return 50.0  # Нейтральне значення при відсутності даних

        rsi_series = df.ta.rsi(length=self._period)
        if rsi_series is None or rsi_series.empty or pd.isna(rsi_series.iloc[-1]):
            return 50.0

        return float(rsi_series.iloc[-1])