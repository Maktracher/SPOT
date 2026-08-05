import pandas as pd
from strategy.indicators.base import IndicatorProtocol


class FearAndGreedIndicator:
    def __init__(self, name: str = "fgi") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def calculate(self, df: pd.DataFrame, context: dict | None = None) -> float:
        if context and "fgi" in context:
            return float(context["fgi"])
        return 50.0