import logging
from dataclasses import dataclass
import pandas as pd

from core.entities import Asset, SignalType, TradingSignal
from strategy.indicators.base import IndicatorProtocol
from strategy.indicators.momentum import RSIIndicator
from strategy.indicators.volatility import ATRIndicator
from strategy.indicators.sentiment import FearAndGreedIndicator
from strategy.rules.base import RuleProtocol
from strategy.rules.conditions import ThresholdRule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScoringConfig:
    buy_score_threshold: float = 25.0  # Сума балів >= 25  -> BUY
    sell_score_threshold: float = -25.0  # Сума балів <= -25 -> SELL

    cancel_buy_score: float = -10.0  # Сума балів <= -10 -> Скасувати BUY
    cancel_sell_score: float = 10.0  # Сума балів >= 10  -> Скасувати SELL


class MultiAssetGridStrategy:
    """
    Двигун оцінки (Scoring Engine):
    1. Збирає значення всіх індикаторів у Feature Vector.
    2. Проганяє Feature Vector через список правил (Rules) та сумує бали.
    3. Приймає рішення про сигнал на основі ScoringConfig.
    """

    def __init__(
            self,
            indicators: list[IndicatorProtocol],
            rules: list[RuleProtocol],
            config: ScoringConfig = ScoringConfig(),
    ) -> None:
        self._indicators = indicators
        self._rules = rules
        self._config = config

    def analyze(self, asset: Asset, ohlcv_df: pd.DataFrame, fgi: int) -> TradingSignal:
        if ohlcv_df.empty:
            logger.warning("Empty dataframe received for %s", asset.symbol)
            return TradingSignal(
                asset=asset,
                signal_type=SignalType.HOLD,
                rsi=50.0,
                fgi=fgi,
                current_price=0.0,
                atr=0.0,
                score=0.0,
            )

        current_price = float(ohlcv_df["close"].iloc[-1])
        context = {"fgi": fgi, "current_price": current_price}

        # 1. Extraction: Обчислення індикаторів
        features: dict[str, float] = {}
        for ind in self._indicators:
            res = ind.calculate(ohlcv_df, context)
            if isinstance(res, dict):
                features.update(res)
            else:
                features[ind.name] = float(res)

        # 2. Scoring: Підрахунок сумарного бала
        total_score = 0.0
        for rule in self._rules:
            total_score += rule.evaluate(features)

        # 3. Decision Matrix: Перетворення балів у торговий сигнал
        signal_type = SignalType.HOLD

        if total_score >= self._config.buy_score_threshold:
            signal_type = SignalType.BUY
        elif total_score <= self._config.sell_score_threshold:
            signal_type = SignalType.SELL
        elif total_score <= self._config.cancel_buy_score:
            signal_type = SignalType.CANCEL_BUY
        elif total_score >= self._config.cancel_sell_score:
            signal_type = SignalType.CANCEL_SELL

        return TradingSignal(
            asset=asset,
            signal_type=signal_type,
            rsi=round(features.get("rsi", 50.0), 2),
            fgi=fgi,
            current_price=current_price,
            atr=features.get("atr", 0.0),
            score=total_score,
        )


# ... existing code ...
def build_default_strategy() -> MultiAssetGridStrategy:
    """
    Factory Function: Створює готову конфігурацію стратегії з балансом балів.
    """
    indicators: list[IndicatorProtocol] = [
        RSIIndicator(period=14, name="rsi"),
        ATRIndicator(period=14, name="atr"),
        FearAndGreedIndicator(name="fgi"),
    ]

    rules: list[RuleProtocol] = [
        ThresholdRule(feature_name="rsi", operator="<=", threshold=25.0, points=20.0, rule_name="RSI_Deep_Oversold"),
        ThresholdRule(feature_name="rsi", operator="<=", threshold=30.0, points=15.0, rule_name="RSI_Oversold"), # Збільшив вагу RSI
        ThresholdRule(feature_name="fgi", operator="<=", threshold=25, points=15.0, rule_name="Extreme_Fear"),
        ThresholdRule(feature_name="fgi", operator="<=", threshold=40, points=5.0, rule_name="Fear"), # Зменшив вагу звичайного страху

        # Правила для продажу (- бали)
        ThresholdRule(feature_name="rsi", operator=">=", threshold=70.0, points=-15.0, rule_name="RSI_Overbought"),
        ThresholdRule(feature_name="rsi", operator=">=", threshold=75.0, points=-20.0, rule_name="RSI_Deep_Overbought"),
        ThresholdRule(feature_name="fgi", operator=">=", threshold=60, points=-5.0, rule_name="Greed"),
        ThresholdRule(feature_name="fgi", operator=">=", threshold=75, points=-15.0, rule_name="Extreme_Greed"),
    ]

    config = ScoringConfig(
        buy_score_threshold=25.0,    # 📌 ЗМІНЕНО З 25.0 НА 20.0: Тепер бот купуватиме раніше (напр. RSI 28 (15) + FGI 35 (5) = 20)
        sell_score_threshold=-25.0,  # -25 балів = SELL
        cancel_buy_score=-15.0,      # Потрібно -15 балів, щоб скасувати купівлю
        cancel_sell_score=15.0,      # Потрібно 15 балів, щоб скасувати продаж
    )

    return MultiAssetGridStrategy(indicators=indicators, rules=rules, config=config)