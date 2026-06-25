import ccxt
import sys
import os
from Telegram_Grid_Bot import TelegramNotifier
from enum import Enum


class Signal(Enum):
    BUY = 1
    SELL = 2
    CANCEL_BUY = 3
    CANCEL_SELL = 4
    HOLD = 5


class StrategyConfig:
    SYMBOL = "BTC/USDT"
    BUY_THRESHOLD = 25
    SELL_THRESHOLD = 75

    FGI_BUY_MAX = 40      # FGI below this value → fear → buying is allowed
    FGI_SELL_MIN = 60     # FGI above this value → greed → selling is allowed

    CANCEL_BUY = 60
    CANCEL_SELL = 40
    BALANCE = 30

    GRID_STEPS = 5
    GRID_PERCENT = 2      # 2% spacing between grid orders

    CHECK_DELAY = 60      # Check the Fear & Greed Index every 60 seconds


def read_api_keys(file_path='api_folder/API.txt'):
    if not os.path.exists(file_path):
        sys.exit(f"ERROR: File '{file_path}' not found.")

    with open(file_path, 'r') as f:
        api_key = f.readline().strip()
        api_secret = f.readline().strip()
        api_key_coin = f.readline().strip()
        telegram_api = f.readline().strip()

    if not api_key or not api_secret:
        sys.exit("ERROR: API keys in API.txt are empty.")

    return api_key, api_secret, api_key_coin, telegram_api


api_key, api_secret, api_key_coin, telegram_api = read_api_keys()

exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret
})

notifier = TelegramNotifier(telegram_api)