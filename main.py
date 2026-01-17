from datetime import datetime, time, timedelta
import os

from config import *
from universe import get_universe
from backtester import backtest
from live_scanner import scan
from reporting import (
    save_trades,
    daily_report,
    weekly_plot,
    monthly_report,
    divergence_alert
)
from telegram_bot import send_message

# -----------------------------
# Setup
# -----------------------------
SYMBOLS = get_universe()

REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)

HEARTBEAT_FILE = os.path.join(REPORT_DIR, "heartbeat.txt")
LAST_BACKTEST_FILE = os.path.join(REPORT_DIR, "last_backtest.txt")
DAILY_REPORT_FILE = os.path.join(REPORT_DIR, "daily_report.txt")
SUMMARY_FILE = os.path.join(REPORT_DIR, "summary.txt")


# -----------------------------
# Helpers
# -----------------------------
def is_market_hours():
    now = datetime.now().time()
    return time(*MARKET_OPEN) <= now <= time(*MARKET_CLOSE)


def get_mode():
    return "BACKTEST" if datetime.now().weekday() >= 5 else "LIVE"


def send_daily_heartbeat(mode):
    today = datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(HEARTBEAT_FILE):
        with open(HEARTBEAT_FILE) as f:
            if f.read().strip() == today:
                return

    send_message(f"🤖 Bot running normally in {mode} mode")
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(today)


def already_ran_today(filepath):
    today = datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(filepath):
        with open(filepath) as f:
            if f.read().strip() == today:
                return True

    with open(filepath, "w") as f:
        f.write(today)

    return False


def send_summary(mode, scanned, signals):
    today = datetime.now().strftime("%Y-%m-%d")

    # Avoid duplicate summary in same day
    if os.path.exists(SUMMARY_FILE):
        with open(SUMMARY_FILE) as f:
            if f.read().strip() == today:
                return

    msg = (
        f"📌 Run Summary\n"
        f"Mode: {mode}\n"
        f"Stocks scanned: {scanned}\n"
        f"Signals generated: {signals}\n"
        f"Time: {datetime.now().strftime('%H:%M:%S')}"
    )

    send_message(msg)

    with open(SUMMARY_FILE, "w") as f:
        f.write(today)


# -----------------------------
# Main Logic
# -----------------------------
MODE = get_mode()
print("Running in mode:", MODE)

send_daily_heartbeat(MODE)

signals_today = 0
stocks_scanned = len(SYMBOLS)


# -----------------------------
# LIVE MODE (Weekdays)
# -----------------------------
if MODE == "LIVE":

    # Scan during market hours
    if is_market_hours():
        for s in SYMBOLS:
            if scan(s):   # <-- assumes scan returns True when signal occurs
                signals_today += 1

    # After market close
    if datetime.now().time() > time(15, 31):

        # Send reports once
        if not already_ran_today(DAILY_REPORT_FILE):
            daily_report()
            divergence_alert()

            # Send summary once per day
            send_summary(MODE, stocks_scanned, signals_today)


# -----------------------------
# BACKTEST MODE (Weekends)
# -----------------------------
elif MODE == "BACKTEST":

    if already_ran_today(LAST_BACKTEST_FILE):
        print("Backtest already ran today. Skipping.")
        exit()

    print("Running backtest...")

    all_trades = []
    for s in SYMBOLS:
        all_trades.extend(backtest(s))

    save_trades(all_trades)

    # Sunday → weekly report
    if datetime.now().weekday() == 6:
        weekly_plot()

    # Month end → monthly report
    tomorrow = datetime.now() + timedelta(days=1)
    if tomorrow.day == 1:
        monthly_report()

    # Weekend summary
    send_summary(MODE, stocks_scanned, len(all_trades))
