from datetime import time
import yfinance as yf
import pandas as pd

# Cache NIFTY data so we don't download it for every stock
_nifty_cache = None


def get_nifty_df(interval="5m", period="15d"):
    global _nifty_cache

    if _nifty_cache is not None:
        return _nifty_cache

    df = yf.download("^NSEI", interval=interval, period=period, progress=False)

    if df.empty:
        return None

    # Simple EMA20 for market bias
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

    _nifty_cache = df
    return df


def is_market_bullish(ts):
    """
    Returns True only if NIFTY is bullish at that timestamp
    """
    nifty = get_nifty_df()

    if nifty is None:
        return False

    # Find nearest timestamp
    if ts not in nifty.index:
        return False

    row = nifty.loc[ts]
    return row["Close"] > row["EMA20"]


def check_signal(df, i):
    """
    Main entry rule with added filters
    """

    row = df.iloc[i]
    ts = df.index[i]

    # -------------------------
    # 1. Time filter (09:20–11:30)
    # -------------------------
    t = ts.time()
    if not (time(9, 20) <= t <= time(11, 30)):
        return False

    # -------------------------
    # 2. Market trend filter (NIFTY bullish)
    # -------------------------
    if not is_market_bullish(ts):
        return False

    # -------------------------
    # 3. Original entry conditions
    # -------------------------
    return (
        row["Close"] > row["VWAP"] and
        row["EMA9"] > row["EMA20"] and
        row["Volume"] > df["Volume"].rolling(20).mean().iloc[i] and
        row["Close"] > df["High"].rolling(10).max().iloc[i - 1]
    )
