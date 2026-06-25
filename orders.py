from Config import StrategyConfig, notifier
from signal_generator import get_atr


def get_price(exchange):
    return exchange.fetch_ticker(StrategyConfig.SYMBOL)["last"]


def get_balance(exchange, asset):
    return exchange.fetch_balance()[asset]["free"]


def create_buy_grid(exchange):
    price = get_price(exchange)
    atr = get_atr(exchange)
    atr_pct = atr / price * 100

    symbol_info = exchange.market(StrategyConfig.SYMBOL)
    min_notional = symbol_info["limits"]["cost"]["min"] or 5
    balance_usdt = get_balance(exchange, "USDT")

    step_usdt = min(StrategyConfig.BALANCE, balance_usdt)

    if step_usdt <= 0:
        notifier.send_message("⛔ Insufficient USDT for BUY grid (balance = 0)")
        print("⛔ Insufficient USDT for BUY grid (balance = 0)")
        return []

    # Hybrid: 2 near ATR levels + 3 Fibonacci levels
    atr_offsets = [1 * atr_pct, 2 * atr_pct]
    fib_offsets = [1.618, 2.618, 4.236]
    levels = atr_offsets + fib_offsets  # 5 total levels

    orders = []
    spent_usdt = 0.0

    for pct in levels:
        if spent_usdt + step_usdt > balance_usdt:
            notifier.send_message("⛔ Insufficient USDT for next grid level")
            print("⛔ Insufficient USDT for next grid level")
            break

        grid_price = price * (1 - pct / 100)
        qty = float(exchange.amount_to_precision(
            StrategyConfig.SYMBOL,
            step_usdt / grid_price
        ))
        grid_price = float(exchange.price_to_precision(
            StrategyConfig.SYMBOL,
            grid_price
        ))

        notional = qty * grid_price

        if notional < min_notional:
            notifier.send_message(
                f"⛔ Order too small: {notional:.2f} < {min_notional:.2f} USDT"
            )
            print(
                f"⛔ Order too small: {notional:.2f} < {min_notional:.2f} USDT"
            )
            continue

        order = exchange.create_limit_buy_order(
            StrategyConfig.SYMBOL,
            qty,
            grid_price
        )

        notifier.send_message(
            f"✅ BUY {qty:.6f} BTC @ {grid_price:.2f} (-{pct:.2f}%)"
        )
        print(
            f"✅ BUY {qty:.6f} BTC @ {grid_price:.2f} (-{pct:.2f}%)"
        )

        orders.append(order["id"])
        spent_usdt += notional

    return orders


def create_sell_grid(exchange):
    price = get_price(exchange)
    atr = get_atr(exchange)
    atr_pct = atr / price * 100

    symbol_info = exchange.market(StrategyConfig.SYMBOL)
    min_notional = symbol_info["limits"]["cost"]["min"] or 5
    balance_btc = get_balance(exchange, "BTC")

    step_usdt = StrategyConfig.BALANCE

    # Mirror logic: 2 ATR + 3 Fibonacci levels upward
    atr_offsets = [1 * atr_pct, 2 * atr_pct]
    fib_offsets = [1.618, 2.618, 4.236]
    levels = atr_offsets + fib_offsets

    orders = []

    for pct in levels:
        grid_price = price * (1 + pct / 100)

        qty = float(exchange.amount_to_precision(
            StrategyConfig.SYMBOL,
            step_usdt / grid_price
        ))
        grid_price = float(exchange.price_to_precision(
            StrategyConfig.SYMBOL,
            grid_price
        ))

        notional = qty * grid_price

        if notional < min_notional:
            notifier.send_message(
                f"⛔ Order too small: {notional:.2f} < {min_notional:.2f} USDT"
            )
            print(
                f"⛔ Order too small: {notional:.2f} < {min_notional:.2f} USDT"
            )
            continue

        if qty > balance_btc:
            notifier.send_message(
                f"⛔ Insufficient BTC: {qty:.6f} > {balance_btc:.6f}"
            )
            print(
                f"⛔ Insufficient BTC: {qty:.6f} > {balance_btc:.6f}"
            )
            break

        order = exchange.create_limit_sell_order(
            StrategyConfig.SYMBOL,
            qty,
            grid_price
        )

        notifier.send_message(
            f"✅ SELL {qty:.6f} BTC @ {grid_price:.2f} (+{pct:.2f}%)"
        )
        print(
            f"✅ SELL {qty:.6f} BTC @ {grid_price:.2f} (+{pct:.2f}%)"
        )

        orders.append(order["id"])
        balance_btc -= qty

    return orders


def cancel_orders(exchange, order_ids):
    for oid in order_ids:
        try:
            exchange.cancel_order(oid, StrategyConfig.SYMBOL)
            print(f"Cancelled order {oid}")
        except Exception as e:
            print(f"Failed to cancel {oid}: {e}")