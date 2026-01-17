import os
import pandas as pd

TRADES_FILE = "trades_log.csv"

COLUMNS = [
    "date", "symbol", "entry_time", "exit_time",
    "entry", "exit", "qty", "pnl", "rr"
]


def save_trades(trades):
    if not trades:
        return

    df = pd.DataFrame(trades)

    # Normalize fields
    df["date"] = df["entry_time"].dt.date
    df["entry_time"] = df["entry_time"].astype(str)
    df["exit_time"] = df.get("exit_time", df["entry_time"]).astype(str)

    if os.path.exists(TRADES_FILE):
        old = pd.read_csv(TRADES_FILE)
        df = pd.concat([old, df], ignore_index=True)

    df[COLUMNS].to_csv(TRADES_FILE, index=False)


def load_trades():
    if not os.path.exists(TRADES_FILE):
        return pd.DataFrame(columns=COLUMNS)

    return pd.read_csv(TRADES_FILE)
