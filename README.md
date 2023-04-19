# Python MACD Bot using Binance API
This is a Python-based trading bot that uses the Moving Average Convergence Divergence (MACD) indicator to make automated trades on Binance exchange. The bot checks every symbol on a 15-minute chart, and can be customized with a user-defined risk-reward ratio.

## Installation
Clone the repository to your local machine:
```bash
git clone https://github.com/ozgurakinj/macdbot.git
```
Install the required dependencies:
```bash
pip install -r requirements.txt
```
Install TA-Lib library for technical analysis:

https://pypi.org/project/TA-Lib/

Update config.py and strategy.py files with your API credentials and preferred strategy.

## Usage
To start the bot, run:
```
python main.py
```
The bot will check every symbol on a 15-minute chart, and make trades based on the MACD indicator.

## Configuration
### Credentials

**config.py** file contains credentials for Binance and Telegram (used for trade alerts)

> **API_KEY:** API Key for Binance

> **API_SECRET:** API Secret for Binance

> **BOT_API:** API Key of your Telegram bot.

> **CHAT_ID:** ID of the chat that is between you and the bot.

### Strategy
**strategy.py** file contains basic strategy variables


> **STOP_LOSS_PERC:** Risk percentage for stop loss.

> **PROFIT_FACTOR:** Value multiplied by stop  loss percentage to set take profit level.

The risk-reward ratio for each trade. For example, if the stop loss value is 2 and the profit factor is 2, he bot will aim to make 4% profit with stop loss set at %2.

> **BLACKLIST:** Symbols to be avoided while trading.

> **WHITELIST:** If set, only whitelisted symbols will be traded.


# Disclaimer
This bot is for educational purposes only and should not be used for real trading without thorough testing and proper risk management. The author of this bot is not responsible for any losses incurred while using this software.
