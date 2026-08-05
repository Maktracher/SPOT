from typing import Protocol, runtime_checkable


@runtime_checkable
class RuleProtocol(Protocol):
    """
    Інтерфейс для торгових правил оцінки (Scoring Rules).
    Отримує Feature Vector (довідник індикаторів) і повертає бали.
    """
    @property
    def name(self) -> str:
        ...

    def evaluate(self, features: dict[str, float]) -> float:
        ...