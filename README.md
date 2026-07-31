# **📈 Multi-Asset Spot Trading Bot (Binance)**

A professional cryptocurrency trading bot for the Binance Spot market. Built on **Clean Architecture** principles, ensuring high scalability, reliability, and isolation of business logic from external integrations.

The bot simultaneously analyzes dozens of assets and utilizes a **Hybrid Grid Strategy** based on a combination of dynamic volatility (ATR), static Fibonacci levels, and market sentiment indicators (RSI, Fear & Greed Index).

## **✨ Key Features**

* **Multi-Asset Support:** Simultaneously monitors and trades a large list of coins (BTC, ETH, SOL, and others).  
* **Hybrid Grid Strategy:** Automatically expands the order grid during high volatility (ATR) using deep Fibonacci extension levels to protect capital.  
* **Strict Risk Management:** Built-in protection against "averaging down to zero" (Max Allocation Limit). The bot will never buy an asset beyond a set limit (e.g., $100).  
* **Order Loop Protection:** The bot recognizes its own active orders on the exchange to prevent duplication and API spamming.  
* **Auto-Time Synchronization:** Built-in fix for the common Binance API Timestamp ahead of server's time issue.  
* **Telegram Notifications:** Instant reports on placed orders, cancellations, risk limit triggers, and system errors.

## **🏗 Architecture (Clean Architecture)**

The project is divided into independent layers:

1. **Core (core/):** Entities, Data Classes, Enums (Asset, TradingSignal, OrderParams).  
2. **Data (data/):** Market data fetching (LiveMarketDataFeed), indicators (RSI, ATR), FGI parsing.  
3. **Strategy (strategy/):** Decision-making logic (when to buy, when to sell).  
4. **Portfolio (portfolio/):** Capital management mathematics, position sizing, and offset calculations (Manager).  
5. **Broker (broker/):** Direct interaction with the exchange via ccxt (order execution, balance checking).  
6. **Infrastructure (infrastructure/):** External services (TelegramNotifier, Config Loader, Logger).  
7. **Engine (runner.py):** The Composition Root that wires all layers together and runs the continuous execution loop (Tick).

## **🧠 Strategy Logic**

The bot uses a conservative approach to buy deep market drawdowns:

* **Entry Condition (BUY):** Current RSI \< 30 **AND** overall Fear & Greed Index \< 40\.  
* **Buy Grid:** 3 equal-volume limit orders (e.g., $30 each).  
* **Order Offsets:** Calculated as Current ATR (%) \* Fibonacci Multiplier.  
  * Utilizes deep multipliers: 2.618, 4.236, 6.854.  
* **Exit Condition (SELL):** Mirrored execution triggered when RSI \> 70\.

## **⚙️ Installation & Setup**

### **1\. Requirements**

* Python 3.10 or higher  
* Libraries from requirements.txt (ccxt, requests, pandas, pandas\_ta, etc.).

pip install \-r requirements.txt

### **2\. API Key Configuration**

Create an api\_folder in the project root and add an API.txt file inside it.

The file must contain exactly 5 lines without extra spaces:

YOUR\_BINANCE\_API\_KEY  
YOUR\_BINANCE\_API\_SECRET  
OPTIONAL\_COIN\_KEY\_OR\_EMPTY\_LINE  
YOUR\_TELEGRAM\_BOT\_TOKEN  
YOUR\_TELEGRAM\_CHAT\_ID

*(Ensure your Binance API Key has Spot Trading permissions, but **disable** Withdrawal permissions).*

### **3\. Adjusting Parameters**

In the runner.py file, you can configure the main engine parameters:

* check\_interval\_seconds=60 — How often the bot scans the market.  
* max\_allocation\_per\_asset\_usdt=100.0 — Maximum amount the bot is allowed to invest in a single coin (drawdown protection).

## **🚀 Execution**

Run the main script:

python runner.py

Upon a successful launch, you will see a connection log in the console, and a message will be sent to your Telegram: 🚀 Trading Engine Started Successfully\!

## **⚠️ Disclaimer**

This software is provided "as is" for educational and research purposes only. Algorithmic cryptocurrency trading carries high financial risks. The author assumes no responsibility for any financial losses incurred from using this bot. Always test the strategy on small amounts before trusting the bot with significant capital.