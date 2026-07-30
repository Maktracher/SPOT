import logging
import ccxt

from core.entities import Asset, Balance, GridOrderParams
from infrastructure.notifier import NotifierProtocol, NullNotifier

logger = logging.getLogger(__name__)


class CCXTExecutionBroker:
    def __init__(
        self,
        exchange: ccxt.Exchange,
        notifier: NotifierProtocol = NullNotifier()
    ) -> None:
        self._exchange = exchange
        self._notifier = notifier
        self._active_orders: dict[Asset, list[str]] = {asset: [] for asset in Asset}

    def has_active_orders(self, asset: Asset) -> bool:
        """Перевіряє, чи виставлена вже сітка для цього активу."""
        return len(self._active_orders.get(asset, [])) > 0

    def fetch_balance(self, currency: str) -> Balance:
        try:
            raw_balance = self._exchange.fetch_balance()
            asset_data = raw_balance.get(currency, {"free": 0.0, "used": 0.0})
            return Balance(
                currency=currency,
                free=float(asset_data.get("free", 0.0)),
                used=float(asset_data.get("used", 0.0)),
            )
        except ccxt.BaseError as e:
            logger.error("Failed to fetch balance for %s: %s", currency, e)
            raise

    def execute_grid_orders(self, params_list: list[GridOrderParams]) -> list[str]:
        placed_order_ids: list[str] = []

        for params in params_list:
            symbol = params.asset.symbol
            try:
                market = self._exchange.market(symbol)
                min_notional = market.get("limits", {}).get("cost", {}).get("min") or 5.0

                qty = float(self._exchange.amount_to_precision(symbol, params.quantity))
                price = float(self._exchange.price_to_precision(symbol, params.price))
                notional = qty * price

                if notional < min_notional:
                    msg = f"⛔ Order rejected for {symbol}: notional {notional:.2f} < min {min_notional:.2f} USDT"
                    logger.warning(msg)
                    self._notifier.send_message(msg)
                    continue

                if params.side.value == "buy":
                    order = self._exchange.create_limit_buy_order(symbol, qty, price)
                    emoji = "✅ 🟢 BUY"
                else:
                    order = self._exchange.create_limit_sell_order(symbol, qty, price)
                    emoji = "✅ 🔴 SELL"

                order_id = str(order["id"])
                placed_order_ids.append(order_id)
                self._active_orders[params.asset].append(order_id)

                success_msg = (
                    f"{emoji} <b>{symbol}</b>\n"
                    f"Qty: {qty}\n"
                    f"Price: {price}\n"
                    f"Offset: -+{params.offset_percent:.2f}%"
                )
                logger.info("Placed order %s: %s", order_id, success_msg.replace('\n', ' '))
                self._notifier.send_message(success_msg)

            except (ccxt.InsufficientFunds, ccxt.InvalidOrder) as e:
                error_msg = f"⛔ Order placement failed [{symbol}]: {e}"
                logger.error(error_msg)
                self._notifier.send_message(error_msg)
            except ccxt.NetworkError as e:
                logger.error("Network failure during order execution [%s]: %s", symbol, e)

        return placed_order_ids

    def cancel_asset_orders(self, asset: Asset) -> None:
        order_ids = self._active_orders.get(asset, [])
        if not order_ids:
            return

        for oid in list(order_ids):
            try:
                self._exchange.cancel_order(oid, asset.symbol)
                msg = f"🚫 Cancelled order {oid} for {asset.symbol}"
                logger.info(msg)
                self._notifier.send_message(msg)
                order_ids.remove(oid)
            except ccxt.OrderNotFound:
                if oid in order_ids:
                    order_ids.remove(oid)
            except ccxt.BaseError as e:
                logger.error("Failed to cancel order %s for %s: %s", oid, asset.symbol, e)

    def sync_open_orders(self, asset: Asset) -> None:
        try:
            open_orders = self._exchange.fetch_open_orders(asset.symbol)
            open_ids = {str(o["id"]) for o in open_orders}
            self._active_orders[asset] = [
                oid for oid in self._active_orders[asset] if oid in open_ids
            ]
        except ccxt.BaseError as e:
            logger.error("Failed to sync open orders for %s: %s", asset.symbol, e)