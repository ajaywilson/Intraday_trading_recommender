from datetime import time
import yfinance as yf
import pandas as pd

# Cache for NIFTY data
_nifty_cache = None


def get_nifty_df(interval="5m", period="15d"):
    global _nifty_cache

    if _nifty_cache is not None:
        return _nifty_cache

    df = yf.download("^NSEI", interval=interval, period=period, progress=False)

    if df.empty:
        return None

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df = df.sort_index()

    _nifty_cache = df
    return df


def is_market_bullish(ts):
    nifty = get_nifty_df()
    if nifty is None or nifty.empty:
        return False

    try:
        idx = nifty.index.get_indexer([ts], method="ffill")[0]
        if idx == -1:
            return False

        row = nifty.iloc[idx]
        return float(row["Close"]) > float(row["EMA20"])
    except Exception:
        return False


def get_opening_range(df):
    """
    Returns OR high and low from 09:15 to 09:30
    """
    or_df = df.between_time("09:15", "09:30")

    if len(or_df) < 3:  # Need at least 3 candles of 5m data
        return None, None

    return or_df["High"].max(), or_df["Low"].min()


def check_signal(df, i):
    row = df.iloc[i]
    ts = df.index[i]
    t = ts.time()

    # Only trade between 09:30 and 11:30
    if not (time(9, 30) <= t <= time(11, 30)):
        return False

    # Market must be bullish
    if not is_market_bullish(ts):
        return False

    # Get opening range
    or_high, or_low = get_opening_range(df)

    if or_high is None:
        return False

    # Conditions for breakout
    bullish_candle = row["Close"] > row["Open"]
    volume_ok = row["Volume"] > df["Volume"].rolling(20).mean().iloc[i]
    breakout = row["Close"] > or_high

    return bullish_candle and volume_ok and breakout
