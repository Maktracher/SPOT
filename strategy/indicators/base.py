from typing import Any, Protocol, runtime_checkable
import pandas as pd


@runtime_checkable
class IndicatorProtocol(Protocol):
    """
    Універсальний інтерфейс для будь-якого індикатора.
    Індикатор ТІЛЬКИ обчислює математичні значення і нічого не знає про торгові сигнали.
    """
    @property
    def name(self) -> str:
        ...

    def calculate(
        self, df: pd.DataFrame, context: dict[str, Any] | None = None
    ) -> float | dict[str, float]:
        ...