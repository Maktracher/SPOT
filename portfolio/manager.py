import logging
from dataclasses import dataclass
from core.entities import Asset, GridOrderParams, OrderSide, TradingSignal

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PortfolioConfig:
    step_balance_usdt: float = 15.0
    # 3 рівні ордерів: ATR множиться на золоті перетини Фібоначчі
    atr_fib_multipliers: tuple[float, ...] = (1.618, 3.236, 6.427)


class PortfolioManager:
    def __init__(self, config: PortfolioConfig = PortfolioConfig()) -> None:
        self._config = config

    def generate_buy_grid_params(
            self, signal: TradingSignal, available_usdt: float
    ) -> list[GridOrderParams]:
        if available_usdt < self._config.step_balance_usdt:
            logger.warning("Insufficient USDT balance for %s grid", signal.asset.symbol)
            return []

        # Визначаємо відсоток ATR від поточної ціни
        atr_pct = (signal.atr / signal.current_price) * 100.0

        # Розраховуємо 3 відступи (наприклад: 1.2%, 1.94%, 3.14%)
        offsets = [m * atr_pct for m in self._config.atr_fib_multipliers]

        orders: list[GridOrderParams] = []
        allocated_usdt = 0.0

        for pct in offsets:
            # Перевірка, чи вистачає депозиту на наступний крок сітки
            if allocated_usdt + self._config.step_balance_usdt > available_usdt:
                break

            target_price = signal.current_price * (1.0 - pct / 100.0)
            quantity = self._config.step_balance_usdt / target_price

            orders.append(
                GridOrderParams(
                    asset=signal.asset,
                    side=OrderSide.BUY,
                    price=target_price,
                    quantity=quantity,
                    offset_percent=pct,
                )
            )
            allocated_usdt += self._config.step_balance_usdt

        return orders

    def generate_sell_grid_params(
            self, signal: TradingSignal, available_base_asset: float
    ) -> list[GridOrderParams]:
        # Визначаємо відсоток ATR від поточної ціни
        atr_pct = (signal.atr / signal.current_price) * 100.0

        # Дзеркальні 3 відступи вгору
        offsets = [m * atr_pct for m in self._config.atr_fib_multipliers]

        orders: list[GridOrderParams] = []
        remaining_asset = available_base_asset

        for pct in offsets:
            target_price = signal.current_price * (1.0 + pct / 100.0)
            quantity = self._config.step_balance_usdt / target_price

            # Перевірка, чи вистачає монет для продажу на цьому рівні
            if quantity > remaining_asset:
                logger.warning("Insufficient %s balance for grid level", signal.asset.base_currency)
                break

            orders.append(
                GridOrderParams(
                    asset=signal.asset,
                    side=OrderSide.SELL,
                    price=target_price,
                    quantity=quantity,
                    offset_percent=pct,
                )
            )
            remaining_asset -= quantity

        return orders