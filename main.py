from backtester import backtest
from live_scanner import scan
from telegram_bot import send_message

MODE = "LIVE"  # BACKTEST or LIVE

symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

if MODE == "BACKTEST":
    for s in symbols:
        trades = backtest(s)
        total = sum(t["pnl"] for t in trades)
        print(s, "Trades:", len(trades), "PnL:", round(total, 2))

elif MODE == "LIVE":
    send_message("🤖 Bot running - scanning market...")
    for s in symbols:
        scan(s)
