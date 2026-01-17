import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from telegram_bot import send_message, send_photo

REPORT = "reports/trades.csv"
PLOT = "reports/weekly.png"


def save_trades(trades):
    if not trades:
        return

    os.makedirs("reports", exist_ok=True)
    df_new = pd.DataFrame(trades)

    if os.path.exists(REPORT):
        df_old = pd.read_csv(REPORT)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(REPORT, index=False)


def load():
    if not os.path.exists(REPORT):
        return pd.DataFrame()

    df = pd.read_csv(REPORT)
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    return df


def daily_report():
    df = load()
    today = datetime.now().date()

    d = df[df["entry_time"].dt.date == today]

    if d.empty:
        send_message("📅 Daily Report\nNo trades today.")
        return

    msg = "📅 Daily Report\n\n"
    for sym, g in d.groupby("symbol"):
        msg += f"{sym}: ₹{round(g['pnl'].sum(), 2)}\n"

    msg += f"\nTotal P&L: ₹{round(d['pnl'].sum(), 2)}"
    send_message(msg)


def weekly_plot():
    df = load()
    week = df[df["entry_time"] > datetime.now() - timedelta(days=7)]

    if week.empty:
        return

    top10 = (
        week.groupby("symbol")["pnl"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    plt.figure(figsize=(8, 4))
    top10.plot(kind="bar")
    plt.title("Top 10 Weekly Performance")
    plt.tight_layout()
    plt.savefig(PLOT)
    plt.close()

    send_message("📊 Weekly Report")
    send_photo(PLOT)


def monthly_report():
    df = load()
    now = datetime.now()

    m = df[
        (df["entry_time"].dt.year == now.year) &
        (df["entry_time"].dt.month == now.month)
    ]

    if m.empty:
        return

    msg = (
        f"📆 Monthly Report\n"
        f"Trades: {len(m)}\n"
        f"Total P&L: ₹{round(m['pnl'].sum(), 2)}"
    )
    send_message(msg)


def divergence_alert():
    df = load()
    week = df[df["entry_time"] > datetime.now() - timedelta(days=7)]

    bt = week[week["mode"] == "BACKTEST"]["pnl"].sum()
    live = week[week["mode"] == "LIVE"]["pnl"].sum()

    if bt != 0:
        divergence = (live - bt) / abs(bt)

        if divergence < -0.3:
            send_message(
                f"⚠️ Strategy divergence alert\n"
                f"Backtest P&L: ₹{round(bt,2)}\n"
                f"Live P&L: ₹{round(live,2)}"
            )


# -----------------------------
# NEW: Backtest performance metrics
# -----------------------------
def backtest_metrics(trades):
    if not trades:
        return None

    df = pd.DataFrame(trades)

    total_pnl = df["pnl"].sum()
    wins = (df["pnl"] > 0).sum()
    total = len(df)

    win_rate = (wins / total) * 100
    avg_pnl = total_pnl / total

    # Equity curve and drawdown
    df["cum_pnl"] = df["pnl"].cumsum()
    df["peak"] = df["cum_pnl"].cummax()
    df["drawdown"] = df["cum_pnl"] - df["peak"]
    max_drawdown = df["drawdown"].min()

    return {
        "trades": total,
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(win_rate, 2),
        "avg_pnl": round(avg_pnl, 2),
        "max_dd": round(max_drawdown, 2)
    }
