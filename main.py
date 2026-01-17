from datetime import datetime, time, timedelta
import os

from config import *
from universe import get_universe
from backtester import backtest, optimize_rr
from reporting import (
    save_trades,
    daily_report,
    weekly_plot,
    monthly_report,
    divergence_alert,
    backtest_metrics
)
from telegram_bot import send_message

SYMBOLS = get_universe()


# -------------------
# Helpers
# -------------------
def is_market_hours():
    now = datetime.now().time()
    return time(*MARKET_OPEN) <= now <= time(*MARKET_CLOSE)


def get_mode():
    return "BACKTEST" if datetime.now().weekday() >= 5 else "LIVE"


# -------------------
# Main
# -------------------
MODE = get_mode()
print("Running in mode:", MODE)

signals_today = 0
stocks_scanned = len(SYMBOLS)


# -------------------
# LIVE MODE
# -------------------
if MODE == "LIVE":

    from live_scanner import scan

    if is_market_hours():
        for s in SYMBOLS:
            if scan(s):
                signals_today += 1

    if datetime.now().time() > time(15, 31):
        daily_report()
        divergence_alert()

        send_message(
            f"📌 Run Summary\n"
            f"Mode: LIVE\n"
            f"Stocks scanned: {stocks_scanned}\n"
            f"Signals generated: {signals_today}"
        )


# -------------------
# BACKTEST MODE
# -------------------
else:
    print("Running weekend backtest...")

    # ---- Normal backtest using configured RR ----
    all_trades = []
    for s in SYMBOLS:
        all_trades.extend(backtest(s))

    save_trades(all_trades)

    metrics = backtest_metrics(all_trades)

    if metrics:
        msg = (
            f"📌 Backtest Summary (RR={RR})\n"
            f"Trades simulated: {metrics['trades']}\n"
            f"Total P&L: ₹ {metrics['total_pnl']}\n"
            f"Win rate: {metrics['win_rate']}%\n"
            f"Avg P&L per trade: ₹ {metrics['avg_pnl']}\n"
            f"Max drawdown: ₹ {metrics['max_dd']}\n\n"
        )
    else:
        msg = "📌 Backtest Summary\nNo trades generated.\n\n"

    # ---- RR Optimization table ----
    rr_results = optimize_rr(SYMBOLS)

    msg += "📊 RR Optimization Table\nRR | Trades | Win% | P&L\n"

    for r in rr_results:
        msg += f"{r['rr']} | {r['trades']} | {r['win_rate']} | ₹{r['pnl']}\n"

    send_message(msg)

    # Weekly / monthly reports
    if datetime.now().weekday() == 6:
        weekly_plot()

    tomorrow = datetime.now() + timedelta(days=1)
    if tomorrow.day == 1:
        monthly_report()
