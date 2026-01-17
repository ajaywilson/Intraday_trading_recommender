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

    # We stop at len(df)-2 because we use i+1 candle for exit logic
    for i in range(30, len(df) - 1):

        # -------------------------
        # ENTRY LOGIC (at candle i close)
        # -------------------------
        if not in_trade and check_signal(df, i):

            entry = float(df.iloc[i]["Close"])
            sl = float(df.iloc[i]["Low"])
            risk = entry - sl

            # Invalid risk (protective)
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
            continue   # CRITICAL: do NOT allow exit on same candle

        # -------------------------
        # EXIT LOGIC (only future candles)
        # -------------------------
        if in_trade:

            next_low = float(df.iloc[i + 1]["Low"])
            next_close = float(df.iloc[i + 1]["Close"])
            next_time = df.index[i + 1].time()

            # Stop loss hit
            if next_low <= trade["sl"]:
                exit_price = trade["sl"]

            # End of day exit (after 15:15 candle)
            elif next_time >= time(15, 15):
                exit_price = next_close

            else:
                continue  # still holding trade

            # Finalize trade
            trade["exit"] = exit_price
            trade["pnl"] = (exit_price - trade["entry"]) * trade["qty"]
            trade["invested"] = trade["entry"] * trade["qty"]

            trades.append(trade)

            # Reset state
            in_trade = False
            trade = None

    return trades
