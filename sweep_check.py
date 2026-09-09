"""
sweep_check.py

Checks the last two closed 1H XAU/USD candles for a sweep:
- Bearish sweep: current candle's high > previous candle's high,
  but current candle closes back BELOW that previous high.
- Bullish sweep: current candle's low < previous candle's low,
  but current candle closes back ABOVE that previous low.

If a sweep is found, sends a Telegram message.

Data source: Twelve Data free API (https://twelvedata.com)
- Free tier: 800 requests/day, plenty for hourly checks.
- Sign up free, get an API key from your dashboard.

Required environment variables (set as GitHub Actions secrets):
  TWELVE_DATA_API_KEY
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
"""

import os
import requests

TWELVE_DATA_API_KEY = os.environ["TWELVE_DATA_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SYMBOL = "XAU/USD"
INTERVAL = "1h"


def get_candles():
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "outputsize": 3,  # last 3 candles is enough (current forming + 2 closed)
        "apikey": TWELVE_DATA_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=15)
    data = resp.json()

    if "values" not in data:
        raise RuntimeError(f"Unexpected API response: {data}")

    # Twelve Data returns most recent first
    return data["values"]


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    resp = requests.post(url, data=payload, timeout=15)
    if resp.status_code != 200:
        print(f"Telegram send failed: {resp.status_code} {resp.text}")
    else:
        print("Telegram message sent.")


def main():
    candles = get_candles()

    # candles[0] = most recent (possibly still forming)
    # candles[1] = last CLOSED candle
    # candles[2] = the one before that (previous candle to compare against)
    last_closed = candles[1]
    prev = candles[2]

    cur_high = float(last_closed["high"])
    cur_low = float(last_closed["low"])
    cur_close = float(last_closed["close"])
    cur_time = last_closed["datetime"]

    prev_high = float(prev["high"])
    prev_low = float(prev["low"])

    print(f"Checking candle at {cur_time}: H={cur_high} L={cur_low} C={cur_close} "
          f"vs prev H={prev_high} L={prev_low}")

    if cur_high > prev_high and cur_close < prev_high:
        msg = (f"Sweep Alert [1H, cloud]: BEARISH sweep at {cur_time} "
               f"(UTC) | swept high {prev_high:.2f} | closed {cur_close:.2f}")
        print(msg)
        send_telegram(msg)
    elif cur_low < prev_low and cur_close > prev_low:
        msg = (f"Sweep Alert [1H, cloud]: BULLISH sweep at {cur_time} "
               f"(UTC) | swept low {prev_low:.2f} | closed {cur_close:.2f}")
        print(msg)
        send_telegram(msg)
    else:
        print("No sweep this candle.")


if __name__ == "__main__":
    main()
