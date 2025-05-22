import ccxt
import time
import requests
import json
import pandas as pd
from datetime import datetime
from scipy.stats import linregress

with open('config.json', 'r') as f:
    config = json.load(f)

TELEGRAM_TOKEN = config["telegram_token"]
CHAT_ID = config["telegram_chat_id"]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

def get_binance_futures_symbols():
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    return [s for s in markets if s.endswith("/USDT") and "future" in markets[s]["type"]]

def fetch_ohlcv(symbol, timeframe="1w", limit=100):
    exchange = ccxt.binance()
    market = exchange.market(symbol)
    return exchange.fetch_ohlcv(market["id"], timeframe=timeframe, limit=limit)

def detect_trendline(highs):
    points = []
    for i in range(1, len(highs) - 1):
        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
            points.append((i, highs[i]))
    if len(points) < config["min_points_trendline"]:
        return None
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    slope, intercept, _, _, _ = linregress(x, y)
    return slope, intercept

def check_pullback(symbol, slope, intercept):
    candles = fetch_ohlcv(symbol, "30m", 100)
    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    for i in range(1, len(df)):
        x = i
        trend_price = slope * x + intercept
        if df["low"].iloc[i] <= trend_price <= df["close"].iloc[i]:
            return True
    return False

def main():
    symbols = get_binance_futures_symbols()
    for symbol in symbols:
        try:
            ohlcv = fetch_ohlcv(symbol, "1w", 100)
            highs = [c[2] for c in ohlcv]
            slope_intercept = detect_trendline(highs)
            if slope_intercept:
                slope, intercept = slope_intercept
                if check_pullback(symbol, slope, intercept):
                    send_telegram_message(f"🚀 *Signal LONG détecté*\n\nCrypto : `{symbol}`\nTrendline 1W cassée + pullback validé en M30.\n\n🟢 Entrée : Market\nSL : sous le dernier creux\nTP : à définir selon structure.")
        except Exception as e:
            print(f"Erreur pour {symbol} : {e}")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(config["scan_interval_minutes"] * 60)
