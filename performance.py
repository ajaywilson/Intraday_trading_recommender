import pandas as pd
from storage import load_trades


def cumulative_metrics():
    df = load_trades()

    if df.empty:
        return None

    df["pnl"] = df["pnl"].astype(float)
    df["cum_pnl"] = df["pnl"].cumsum()

    total_trades = len(df)
    wins = (df["pnl"] > 0).sum()
    win_rate = round(wins / total_trades * 100, 2)

    total_pnl = round(df["pnl"].sum(), 2)
    avg_pnl = round(df["pnl"].mean(), 2)

    df["peak"] = df["cum_pnl"].cummax()
    df["drawdown"] = df["cum_pnl"] - df["peak"]
    max_dd = round(df["drawdown"].min(), 2)

    return {
        "trades": total_trades,
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "avg_pnl": avg_pnl,
        "max_dd": max_dd,
        "last_cum_pnl": round(df["cum_pnl"].iloc[-1], 2),
    }
