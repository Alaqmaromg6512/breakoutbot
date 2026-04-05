import time
import pandas as pd
import requests
from binance.client import Client

# === CONFIG ===

TELEGRAM_TOKEN = "7231685805:AAGlkWIcSn6EtO8lZ5rINtcUZG0CdwTMsuo"
CHAT_ID = "1936312623"

INTERVAL = Client.KLINE_INTERVAL_5MINUTE
LOOKBACK = 20

client = Client()

# === TELEGRAM ===
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# === GET ALL USDT PAIRS ===
def get_usdt_pairs():
    exchange_info = client.get_exchange_info()
    symbols = []

    for s in exchange_info["symbols"]:
        if s["quoteAsset"] == "USDT" and s["status"] == "TRADING":
            symbols.append(s["symbol"])

    return symbols

SYMBOLS = get_usdt_pairs()

# === GET DATA ===
def get_data(symbol):
    klines = client.get_klines(symbol=symbol, interval=INTERVAL, limit=LOOKBACK+2)
    df = pd.DataFrame(klines, columns=[
        "time","open","high","low","close","volume",
        "ct","qv","nt","tb","tq","ignore"
    ])
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    return df

# === BREAKOUT LOGIC ===
def check_breakout(symbol):
    df = get_data(symbol)

    highest_high = df["high"][:-2].max()
    lowest_low = df["low"][:-2].min()

    prev_close = df["close"].iloc[-2]
    last_close = df["close"].iloc[-1]

    if prev_close <= highest_high and last_close > highest_high:
        return "LONG"

    elif prev_close >= lowest_low and last_close < lowest_low:
        return "SHORT"

    return None

# === ANTI-SPAM ===
last_alerts = {}

# === MAIN LOOP ===
print("Bot running... 🚀")

while True:
    for symbol in SYMBOLS:
        try:
            result = check_breakout(symbol)

            if result:
                if last_alerts.get(symbol) != result:
                    msg = f"""
🚨 Breakout Detected

Pair: {symbol}
Type: {result}
Timeframe: 5m

Check on TradingView
"""
                    print(msg)
                    send_telegram(msg)
                    last_alerts[symbol] = result

        except Exception as e:
            print(f"Error with {symbol}: {e}")

    time.sleep(60)
