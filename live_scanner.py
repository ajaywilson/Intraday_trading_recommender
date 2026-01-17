from data import fetch_data
from indicators import add_indicators
from strategy import check_signal
from telegram_bot import send_message
from config import INTERVAL, PERIOD_LIVE

def scan(symbol):
    df = fetch_data(symbol, INTERVAL, PERIOD_LIVE)

    if df.empty or len(df) < 50:
        return

    df = add_indicators(df).dropna()

    if check_signal(df, len(df)-1):
        send_message(f"📈 Intraday Signal detected on {symbol}")
