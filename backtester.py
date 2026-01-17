from data import fetch_data
from indicators import add_indicators
from strategy import check_signal
from execution import ExecutionEngine
from config import CAPITAL, RISK_PER_TRADE, INTERVAL, PERIOD_BACKTEST
from datetime import time

def backtest(symbol):
    df = fetch_data(symbol, INTERVAL, PERIOD_BACKTEST)

    if df.empty or len(df) < 100:
        return []

    df = add_indicators(df).dropna()
    executor = ExecutionEngine()

    trades = []
    in_trade = False

    for i in range(30, len(df)):
        if not in_trade and check_signal(df, i):
            entry = df.iloc[i]["Close"]
            sl = df.iloc[i]["Low"]
            risk = entry - sl
            if risk <= 0:
                continue

            qty = int((CAPITAL * RISK_PER_TRADE) // risk)
            if qty <= 0:
                continue

            exec_price = executor.execute_buy(entry, qty)

            trade = {
                "entry": exec_price,
                "sl": sl,
                "qty": qty,
                "entry_time": df.index[i]
            }
            in_trade = True

        if in_trade:
            low = df.iloc[i]["Low"]
            if low <= trade["sl"] or df.index[i].time() >= time(15, 15):
                exit_price = trade["sl"] if low <= trade["sl"] else df.iloc[i]["Close"]
                trade["exit"] = exit_price
                trade["pnl"] = (exit_price - trade["entry"]) * trade["qty"]
                trades.append(trade)
                in_trade = False

    return trades
