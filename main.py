from datetime import datetime, time, timedelta
from config import *
from universe import get_universe
from backtester import backtest
from live_scanner import scan
from reporting import *
from telegram_bot import send_message

SYMBOLS = get_universe()

def is_market_hours():
    now = datetime.now().time()
    return time(*MARKET_OPEN) <= now <= time(*MARKET_CLOSE)

MODE = "BACKTEST" if datetime.now().weekday() >= 5 else "LIVE"

if MODE == "LIVE":
    if is_market_hours():
        for s in SYMBOLS:
            scan(s)

    if datetime.now().time() > time(15, 31):
        daily_report()
        divergence_alert()

elif MODE == "BACKTEST":
    all_trades = []
    for s in SYMBOLS:
        all_trades.extend(backtest(s))
    save_trades(all_trades)

    if datetime.now().weekday() == 6:
        weekly_plot()

    if (datetime.now() + timedelta(days=1)).day == 1:
        monthly_report()
