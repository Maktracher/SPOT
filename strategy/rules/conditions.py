from dataclasses import dataclass
from strategy.rules.base import RuleProtocol


@dataclass(frozen=True)
class ThresholdRule:
    """
    Правило порогового значення.
    Наприклад: Якщо rsi <= 30 -> додати +15.0 балів до сигналу BUY.
    """
    feature_name: str
    threshold: float
    operator: str  # "<", "<=", ">", ">=", "=="
    points: float
    rule_name: str = ""

    @property
    def name(self) -> str:
        return self.rule_name or f"{self.feature_name}_{self.operator}_{self.threshold}"

    def evaluate(self, features: dict[str, float]) -> float:
        value = features.get(self.feature_name)
        if value is None:
            return 0.0

        matched = False
        if self.operator == "<" and value < self.threshold:
            matched = True
        elif self.operator == "<=" and value <= self.threshold:
            matched = True
        elif self.operator == ">" and value > self.threshold:
            matched = True
        elif self.operator == ">=" and value >= self.threshold:
            matched = True
        elif self.operator == "==" and value == self.threshold:
            matched = True

        return self.points if matched else 0.0