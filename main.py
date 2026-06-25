import time
from Config import exchange, StrategyConfig, Signal,notifier
from signal_generator import generate_signal
from orders import create_buy_grid,create_sell_grid,cancel_orders

class GridTrader:
    def __init__(self):
        self.buy_orders = []
        self.sell_orders = []

    def update_orders(self):

        open_orders = exchange.fetch_open_orders(
            StrategyConfig.SYMBOL
        )

        open_ids = {
            o["id"]
            for o in open_orders
        }

        self.buy_orders = [
            oid
            for oid in self.buy_orders
            if oid in open_ids
        ]

        self.sell_orders = [
            oid
            for oid in self.sell_orders
            if oid in open_ids
        ]

    def execute(self, signal):

        if signal == Signal.BUY:
            cancel_orders(
                exchange,
                self.sell_orders
            )
            self.sell_orders = []
            if not self.buy_orders:

                self.buy_orders = create_buy_grid(exchange)

        elif signal == Signal.SELL:
            cancel_orders(
                exchange,
                self.buy_orders
            )
            self.buy_orders = []

            if not self.sell_orders:

                self.sell_orders = create_sell_grid(exchange)

        elif signal == Signal.CANCEL_BUY:

            cancel_orders(
                exchange,
                self.buy_orders
            )

            self.buy_orders = []

        elif signal == Signal.CANCEL_SELL:

            cancel_orders(

                exchange,

                self.sell_orders

            )

            self.sell_orders = []


def main():
    exchange.load_markets()
    trader = GridTrader()

    while True:
        try:
            trader.update_orders()
            signal = generate_signal(exchange)
            trader.execute(signal)
        except Exception as e:
            notifier.send_message(f"❌ Помилка бота: {e}")
            print(f"Помилка: {e}")
        time.sleep(StrategyConfig.CHECK_DELAY)


if __name__ == "__main__":
    main()
