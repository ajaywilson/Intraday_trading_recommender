from data import fetch_data
from indicators import add_indicators
from strategy import check_signal
from execution import ExecutionEngine
from config import *
from datetime import time


# -------------------------------
# Normal backtest (uses config.RR)
# -------------------------------
def backtest(symbol):
    return _run_backtest(symbol, rr=RR)


# -------------------------------
# Internal engine
# -------------------------------
def _run_backtest(symbol, rr):
    df = fetch_data(symbol, INTERVAL, PERIOD_BACKTEST)

    if df.empty or len(df) < 100:
        return []

    df = add_indicators(df).dropna().copy()

    executor = ExecutionEngine()
    trades = []

    in_trade = False
    trade = None

    for i in range(30, len(df) - 1):

        # ENTRY
        if not in_trade and check_signal(df, i):

            entry = float(df.iloc[i]["Close"])
            sl = float(df.iloc[i]["Low"])
            risk = entry - sl

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
            continue

        # EXIT
        if in_trade:
            next_low = float(df.iloc[i + 1]["Low"])
            next_high = float(df.iloc[i + 1]["High"])
            next_close = float(df.iloc[i + 1]["Close"])
            next_time = df.index[i + 1].time()

            risk = trade["entry"] - trade["sl"]
            target = trade["entry"] + rr * risk

            if next_low <= trade["sl"]:
                exit_price = trade["sl"]

            elif next_high >= target:
                exit_price = target

            elif next_time >= time(15, 15):
                exit_price = next_close

            else:
                continue

            trade["exit"] = exit_price
            trade["exit_time"] = df.index[i + 1]
            trade["pnl"] = (exit_price - trade["entry"]) * trade["qty"]
            trade["invested"] = trade["entry"] * trade["qty"]
            trade["rr"] = rr

            trades.append(trade)

            in_trade = False
            trade = None

    return trades


# -------------------------------
# RR OPTIMIZATION (research tool)
# -------------------------------
def optimize_rr(symbols):
    results = []

    for rr in RR_OPT_VALUES:
        all_trades = []

        for s in symbols:
            all_trades.extend(_run_backtest(s, rr))

        if not all_trades:
            continue

        total_pnl = sum(t["pnl"] for t in all_trades)
        wins = sum(1 for t in all_trades if t["pnl"] > 0)
        total = len(all_trades)

        win_rate = round((wins / total) * 100, 2)

        results.append({
            "rr": rr,
            "trades": total,
            "win_rate": win_rate,
            "pnl": round(total_pnl, 2)
        })

    return results

