import os, pandas as pd, matplotlib.pyplot as plt
from datetime import datetime, timedelta
from telegram_bot import send_message, send_photo

REPORT = "reports/trades.csv"
PLOT = "reports/weekly.png"

def save_trades(trades):
    if not trades: return
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
        send_message("📅 No trades today.")
        return

    msg = "📅 Daily Report\n\n"
    for sym, g in d.groupby("symbol"):
        msg += f"{sym}: ₹{round(g['pnl'].sum(),2)}\n"
    msg += f"\nTotal: ₹{round(d['pnl'].sum(),2)}"
    send_message(msg)

def weekly_plot():
    df = load()
    week = df[df["entry_time"] > datetime.now() - timedelta(days=7)]
    if week.empty: return

    top10 = week.groupby("symbol")["pnl"].sum().sort_values(ascending=False).head(10)

    plt.figure(figsize=(8,4))
    top10.plot(kind="bar")
    plt.title("Top 10 Weekly")
    plt.tight_layout()
    plt.savefig(PLOT)
    plt.close()

    send_message("📊 Weekly Report")
    send_photo(PLOT)

def monthly_report():
    df = load()
    now = datetime.now()
    m = df[(df["entry_time"].dt.year == now.year) & (df["entry_time"].dt.month == now.month)]
    if m.empty: return

    send_message(f"📆 Monthly Report\nTrades: {len(m)}\nPnL: ₹{round(m['pnl'].sum(),2)}")

def divergence_alert():
    df = load()
    week = df[df["entry_time"] > datetime.now() - timedelta(days=7)]
    bt = week[week["mode"]=="BACKTEST"]["pnl"].sum()
    live = week[week["mode"]=="LIVE"]["pnl"].sum()

    if bt and (live - bt)/abs(bt) < -0.3:
        send_message(f"⚠️ Divergence Alert\nBT: {bt}\nLIVE: {live}")
