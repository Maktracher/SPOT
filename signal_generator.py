import pandas as pd
from Config import exchange, Signal, StrategyConfig
import requests


def get_rsi(exchange, symbol="BTC/USDT", timeframe="1h", limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(
        ohlcv,
        columns=["time", "open", "high", "low", "close", "volume"]
    )
    df["close"] = df["close"].astype(float)

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder smoothing (standard RSI, alpha = 1/14)
    roll_up = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    roll_down = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()

    rs = roll_up / roll_down
    rsi = 100.0 - (100.0 / (1.0 + rs))
    current_rsi = round(rsi.iloc[-1], 2)

    print(f"RSI = {current_rsi}")
    return current_rsi


def get_fgi():
    try:
        fgi = requests.get(
            "https://api.alternative.me/fng/?limit=1",
            timeout=5
        ).json()

        value = int(fgi["data"][0]["value"])
        print(f"FGI = {value}")
        return value

    except Exception as e:
        print(f"FGI unavailable: {e}, using neutral value 50")
        return 50  # HOLD zone, bot does nothing


def get_atr(exchange, symbol="BTC/USDT", timeframe="1h", period=14):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=period + 1)
    df = pd.DataFrame(
        ohlcv,
        columns=["time", "open", "high", "low", "close", "volume"]
    )

    df["tr"] = (df["high"] - df["low"]).abs()
    atr = df["tr"].rolling(period).mean().iloc[-1]

    print(atr)
    return atr


def generate_signal(exchange):
    fgi = get_fgi()
    rsi = get_rsi(exchange)

    if rsi <= StrategyConfig.BUY_THRESHOLD and fgi <= StrategyConfig.FGI_BUY_MAX:
        return Signal.BUY

    elif rsi >= StrategyConfig.SELL_THRESHOLD and fgi >= StrategyConfig.FGI_SELL_MIN:
        return Signal.SELL

    elif rsi >= StrategyConfig.CANCEL_BUY:
        return Signal.CANCEL_BUY

    elif rsi <= StrategyConfig.CANCEL_SELL:
        return Signal.CANCEL_SELL

    return Signal.HOLD


if __name__ == "__main__":
    value = get_fgi()
    print(value)

    rsi = get_rsi(exchange)
    print(rsi)