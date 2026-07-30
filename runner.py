import logging
import time
import ccxt

from core.entities import Asset, SignalType
from data.feed import LiveMarketDataFeed
from strategy.grid_strategy import MultiAssetGridStrategy
from portfolio.manager import PortfolioManager
from broker.executor import CCXTExecutionBroker
from infrastructure.config import load_api_keys, setup_logging
from infrastructure.notifier import TelegramNotifier

logger = logging.getLogger("Engine")


class MultiAssetTradingEngine:
    def __init__(
            self,
            data_feed: LiveMarketDataFeed,
            strategy: MultiAssetGridStrategy,
            portfolio: PortfolioManager,
            broker: CCXTExecutionBroker,
            notifier: TelegramNotifier,
            check_interval_seconds: int = 60,
            max_allocation_per_asset_usdt: float = 70.0,  # 📌 ДОДАНО: Максимальна сума в $ на одну монету
    ) -> None:
        self._data_feed = data_feed
        self._strategy = strategy
        self._portfolio = portfolio
        self._broker = broker
        self._notifier = notifier
        self._check_interval = check_interval_seconds
        self._max_allocation = max_allocation_per_asset_usdt

    def run_tick(self) -> None:
        logger.info("--- Starting market analysis tick for %d assets ---", len(Asset))

        fgi = self._data_feed.get_fgi()

        for asset in Asset:
            try:
                if not self._data_feed.is_market_open(asset):
                    continue

                self._broker.sync_open_orders(asset)
                ohlcv_df = self._data_feed.get_ohlcv(asset, timeframe="1h", limit=100)
                signal = self._strategy.analyze(asset, ohlcv_df, fgi)

                # 📌 ДОДАНО: Рахуємо, скільки грошей (в USDT) вже вкладено в цю монету
                base_balance = self._broker.fetch_balance(asset.base_currency)
                # total = free (просто лежать) + used (заблоковані у SELL ордерах)
                total_base_coins = base_balance.free + base_balance.used
                position_value_usdt = total_base_coins * signal.current_price

                logger.info(
                    "Asset: %-10s | Price: %-9.4f | Signal: %-11s | RSI: %-5.2f | Hold: $%.2f",
                    asset.symbol, signal.current_price, signal.signal_type.name, signal.rsi, position_value_usdt
                )

                # 5. Order Execution Flow based on Signal
                if signal.signal_type == SignalType.BUY:
                    if self._broker.has_active_orders(asset):
                        logger.debug("Buy grid already active for %s.", asset.symbol)

                    # 📌 ДОДАНО: Захист від нескінченної закупки падіння
                    elif position_value_usdt >= self._max_allocation * 0.95:  # 0.95 (95%) - це буфер на дрібні зміни ціни
                        msg = f"🛡️ <b>Risk Limit:</b> Вже куплено {asset.symbol} на ${position_value_usdt:.2f}. Ігнорую падіння."
                        logger.warning("Max allocation reached for %s (%.2f USDT). Ignoring BUY.", asset.symbol,
                                       position_value_usdt)

                        # Якщо хочеш отримувати сповіщення, коли монета досягла ліміту (можна закоментувати, щоб не спамило)
                        # self._notifier.send_message(msg)

                    else:
                        self._broker.cancel_asset_orders(asset)
                        usdt_balance = self._broker.fetch_balance("USDT")

                        # 📌 ДОДАНО: Бот витратить лише залишок від дозволеного ліміту
                        allowed_to_spend = min(usdt_balance.free, self._max_allocation - position_value_usdt)

                        buy_params = self._portfolio.generate_buy_grid_params(signal, allowed_to_spend)
                        self._broker.execute_grid_orders(buy_params)

                elif signal.signal_type == SignalType.SELL:
                    if not self._broker.has_active_orders(asset):
                        self._broker.cancel_asset_orders(asset)
                        # Для продажу беремо тільки .free (незаблоковані) монети
                        sell_params = self._portfolio.generate_sell_grid_params(signal, base_balance.free)
                        self._broker.execute_grid_orders(sell_params)
                    else:
                        logger.debug("Sell grid already active for %s.", asset.symbol)

                elif signal.signal_type == SignalType.CANCEL_BUY:
                    self._broker.cancel_asset_orders(asset)

                elif signal.signal_type == SignalType.CANCEL_SELL:
                    self._broker.cancel_asset_orders(asset)

            except ccxt.BaseError as e:
                logger.error("Exchange error processing asset %s: %s", asset.symbol, e)
            except Exception as e:
                err_msg = f"⚠️ Critical failure processing {asset.symbol}: {e}"
                logger.exception(err_msg)
                self._notifier.send_message(err_msg)

    def start(self) -> None:
        logger.info("Initializing Engine Loop...")
        self._notifier.send_message("🚀 <b>Trading Engine Started Successfully!</b>")
        while True:
            try:
                self.run_tick()
            except Exception as e:
                logger.critical("Fatal loop exception: %s", e, exc_info=True)
                self._notifier.send_message(f"🚨 <b>FATAL ENGINE ERROR:</b> {e}")

            time.sleep(self._check_interval)


def main() -> None:
    setup_logging()
    api_keys = load_api_keys()

    # Створюємо нотифікатор
    notifier = TelegramNotifier(
        bot_token=api_keys.telegram_bot_token,
        chat_id=None  # Якщо у тебе chat_id прописаний у самому токені або надсилається на дефолтний канал
    )

    exchange = ccxt.binance({
        "apiKey": api_keys.api_key,
        "secret": api_keys.api_secret,
        "enableRateLimit": True,
        "options": {
            "adjustForTimeDifference": True,
            "recvWindow": 10000,
        }
    })

    logger.info("Synchronizing time difference with Binance...")
    exchange.load_time_difference()

    logger.info("Loading exchange markets...")
    exchange.load_markets()

    # Composition Root з прокиданням нотифікатора
    data_feed = LiveMarketDataFeed(exchange)
    strategy = MultiAssetGridStrategy()
    portfolio = PortfolioManager()
    broker = CCXTExecutionBroker(exchange, notifier=notifier)

    engine = MultiAssetTradingEngine(
        data_feed=data_feed,
        strategy=strategy,
        portfolio=portfolio,
        broker=broker,
        notifier=notifier,
        check_interval_seconds=60,
    )

    engine.start()


if __name__ == "__main__":
    main()