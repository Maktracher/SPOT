# SPOT Trading Bot (Grid + RSI + FGI Strategy)

Automated cryptocurrency spot trading bot built on top of **ccxt Binance API**, combining:
- Grid trading system
- RSI momentum indicator
- Fear & Greed Index filter
- ATR-based volatility adaptation
- Telegram notifications

---

## ⚙️ Strategy Overview

The bot executes trades based on a hybrid logic:

### Entry Conditions
- **BUY signal**
  - RSI ≤ BUY_THRESHOLD
  - Fear & Greed Index ≤ FGI_BUY_MAX (fear zone)

- **SELL signal**
  - RSI ≥ SELL_THRESHOLD
  - Fear & Greed Index ≥ FGI_SELL_MIN (greed zone)

### Risk Controls
- Automatic order cancellation based on RSI thresholds
- Grid recalculation when market regime changes
- Minimum notional filter (exchange constraints)

---

## 📊 Indicators Used

### RSI (Relative Strength Index)
- Wilder smoothing method
- Timeframe: configurable (default 1h)
- Used for momentum detection

### Fear & Greed Index (FGI)
- External API: alternative.me
- Measures market sentiment

### ATR (Average True Range)
- Used to define dynamic grid spacing
- Combined with Fibonacci levels for order placement

---

## 📦 Grid System

The bot creates two directional grids:

### Buy Grid
- Orders placed below current price
- Levels:
  - ATR-based offsets
  - Fibonacci extensions (1.618, 2.618, 4.236)
- Dynamically adjusts based on available USDT balance

### Sell Grid
- Mirror logic above current price
- Uses available BTC balance

---

## 🧠 Signal Engine

Located in `signal_generator.py`:

Priority logic:
1. BUY / SELL (RSI + FGI confirmation)
2. CANCEL BUY (RSI overbought region)
3. CANCEL SELL (RSI oversold region)
4. HOLD (no action)

---

## 🔌 Dependencies

```bash
pip install ccxt pandas requests
