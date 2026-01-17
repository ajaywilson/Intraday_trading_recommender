from data import fetch_data
from indicators import add_indicators
from strategy import check_signal
from execution import ExecutionEngine
from config import *
from datetime import time


def backtest(symbol):
    df = fetch_data(symbol, INTERVAL, PERIOD_BACKTEST)

    if df.empty or len(df) < 100:
        return []

    df = add_indicators(df).dropna().copy()

    executor = ExecutionEngine()
    trades = []

    in_trade = False
    trade = None

    # Loop until second last candle because we use i+1 for execution
    for i in range(30, len(df) - 1):

        # ------------------------
        # ENTRY (on candle i close)
        # ------------------------
        if not in_trade and check_signal(df, i):

            entry = float(df.iloc[i]["Close"])
            sl = float(df.iloc[i]["Low"])
            risk = entry - sl

            # Skip bad trades
            if risk <= 0:
                continue

            qty = int((CAPITAL * RISK_PER_TRADE) // risk)
            if qty <= 0:
                continue

            exec_price = executor.execute_buy(entry, qty)

            trade = {
                "symbol": symbol,
                "entry": exec_price,
                "sl": sl,
                "qty": qty,
                "entry_time": df.index[i],
                "mode": "BACKTEST"
            }

            in_trade = True
            continue  # IMPORTANT: don't allow exit on same candle

        # ------------------------
        # EXIT LOGIC (future candles only)
        # ------------------------
        if in_trade:

            next_low = float(df.iloc[i + 1]["Low"])
            next_high = float(df.iloc[i + 1]["High"])
            next_close = float(df.iloc[i + 1]["Close"])
            next_time = df.index[i + 1].time()

            # Risk and target
            risk = trade["entry"] - trade["sl"]
            target = trade["entry"] + 1.5 * risk

            # Stop loss hit
            if next_low <= trade["sl"]:
                exit_price = trade["sl"]

            # Target hit
            elif next_high >= target:
                exit_price = target

            # End of day exit
            elif next_time >= time(15, 15):
                exit_price = next_close

            else:
                continue  # still in trade

            # Finalize trade
            trade["exit"] = exit_price
            trade["pnl"] = (exit_price - trade["entry"]) * trade["qty"]
            trade["invested"] = trade["entry"] * trade["qty"]

            trades.append(trade)

            # Reset state
            in_trade = False
            trade = None

    return trades
