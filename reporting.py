import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from telegram_bot import send_message, send_photo

REPORT = "reports/trades.csv"
PLOT = "reports/weekly.png"


# -----------------------------
# Save trades (safe + consistent)
# -----------------------------
def save_trades(trades):
    if not trades:
        return

    os.makedirs("reports", exist_ok=True)
    df_new = pd.DataFrame(trades)

    # Ensure required columns exist
    for col in ["symbol", "entry_time", "exit_time", "pnl", "mode"]:
        if col not in df_new.columns:
            df_new[col] = None

    if os.path.exists(REPORT):
        df_old = pd.read_csv(REPORT)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(REPORT, index=False)


# -----------------------------
# Safe loader
# -----------------------------
def load():
    if not os.path.exists(REPORT):
        return pd.DataFrame()

    df = pd.read_csv(REPORT)

    # Safely parse datetime if column exists
    if "entry_time" in df.columns:
        df["entry_time"] = pd.to_datetime(df["entry_time"], errors="coerce")

    return df


# -----------------------------
# Daily report (never crashes)
# -----------------------------
def daily_report():
    df = load()
    if df.empty:
        return

    today = datetime.now().date()

    if "entry_time" not in df.columns:
        return

    d = df[df["entry_time"].dt.date == today]

    if d.empty:
        send_message("📅 Daily Report\nNo trades today.")
        return

    msg = "📅 Daily Report\n\n"
    for sym, g in d.groupby("symbol"):
        msg += f"{sym}: ₹{round(g['pnl'].sum(), 2)}\n"

    msg += f"\nTotal P&L: ₹{round(d['pnl'].sum(), 2)}"
    send_message(msg)


# -----------------------------
# Weekly top-10 plot
# -----------------------------
def weekly_plot():
    df = load()
    if df.empty or "entry_time" not in df.columns:
        return

    week = df[df["entry_time"] > datetime.now() - timedelta(days=7)]

    if week.empty:
        return

    top10 = (
        week.groupby("symbol")["pnl"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    os.makedirs("reports", exist_ok=True)

    plt.figure(figsize=(8, 4))
    top10.plot(kind="bar")
    plt.title("Top 10 Weekly Performance")
    plt.tight_layout()
    plt.savefig(PLOT)
    plt.close()

    send_message("📊 Weekly Report")
    send_photo(PLOT)


# -----------------------------
# Monthly summary
# -----------------------------
def monthly_report():
    df = load()
    if df.empty or "entry_time" not in df.columns:
        return

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


# -----------------------------
# Backtest vs Live divergence alert
# -----------------------------
def divergence_alert():
    df = load()
    if df.empty or "entry_time" not in df.columns or "mode" not in df.columns:
        return

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
# Backtest performance metrics (safe)
# -----------------------------
def backtest_metrics(trades):
    if not trades:
        return None

    df = pd.DataFrame(trades)

    if "pnl" not in df.columns:
        return None

    total_pnl = df["pnl"].sum()
    wins = (df["pnl"] > 0).sum()
    total = len(df)

    win_rate = (wins / total) * 100
    avg_pnl = total_pnl / total

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
