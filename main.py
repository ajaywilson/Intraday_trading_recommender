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
from storage import save_trades
from performance import cumulative_metrics


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

    all_trades = []
    for s in SYMBOLS:
        all_trades.extend(backtest(s))

    # Save trades permanently
    save_trades(all_trades)

    # Normal backtest metrics (this run only)
    metrics = backtest_metrics(all_trades)

    msg = ""
    if metrics:
        msg += (
            f"📌 Backtest Summary (this run, RR={RR})\n"
            f"Trades: {metrics['trades']}\n"
            f"P&L: ₹ {metrics['total_pnl']}\n"
            f"Win rate: {metrics['win_rate']}%\n"
            f"Avg P&L: ₹ {metrics['avg_pnl']}\n"
            f"Max DD: ₹ {metrics['max_dd']}\n\n"
        )

    # Cumulative performance across ALL days
    cum = cumulative_metrics()

    if cum:
        msg += (
            f"📈 Cumulative Paper Trading Performance\n"
            f"Total trades: {cum['trades']}\n"
            f"Total P&L: ₹ {cum['total_pnl']}\n"
            f"Win rate: {cum['win_rate']}%\n"
            f"Avg P&L/trade: ₹ {cum['avg_pnl']}\n"
            f"Max drawdown: ₹ {cum['max_dd']}\n\n"
        )

    # RR Optimization
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

