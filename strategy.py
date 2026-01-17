from datetime import time
import yfinance as yf
import pandas as pd

_nifty_cache = None


def get_nifty_df(interval="5m", period="15d"):
    global _nifty_cache

    if _nifty_cache is not None:
        return _nifty_cache

    df = yf.download("^NSEI", interval=interval, period=period, progress=False)

    if df.empty:
        return None

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

    # Ensure sorted index
    df = df.sort_index()

    _nifty_cache = df
    return df


def is_market_bullish(ts):
    """
    Returns True if NIFTY is bullish at or just before timestamp ts
    """
    nifty = get_nifty_df()

    if nifty is None or nifty.empty:
        return False

    # Find nearest earlier timestamp
    try:
        idx = nifty.index.get_indexer([ts], method="ffill")[0]
        if idx == -1:
            return False

        row = nifty.iloc[idx]
        return float(row["Close"]) > float(row["EMA20"])

    except Exception:
        return False


def check_signal(df, i):
    row = df.iloc[i]
    ts = df.index[i]

    # -------------------------
    # 1. Time filter (09:20–11:30)
    # -------------------------
    t = ts.time()
    if not (time(9, 20) <= t <= time(11, 30)):
        return False

    # -------------------------
    # 2. Market trend filter
    # -------------------------
    if not is_market_bullish(ts):
        return False

    # -------------------------
    # 3. Original entry logic
    # -------------------------
    return (
        row["Close"] > row["VWAP"] and
        row["EMA9"] > row["EMA20"] and
        row["Volume"] > df["Volume"].rolling(20).mean().iloc[i] and
        row["Close"] > df["High"].rolling(10).max().iloc[i - 1]
    )
