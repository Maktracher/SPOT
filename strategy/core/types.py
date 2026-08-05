from dataclasses import dataclass
from enum import Enum, auto
import pandas as pd

from core.entities import Asset  # Імпорт Asset із загальних моделей


class SignalType(Enum):
    BUY = auto()
    SELL = auto()
    HOLD = auto()
    CANCEL_BUY = auto()
    CANCEL_SELL = auto()


@dataclass(frozen=True)
class TradingSignal:
    asset: Asset
    signal_type: SignalType
    rsi: float
    fgi: int
    current_price: float
    atr: float
    score: float = 0.0  # Підсумковий бал системи оцінки