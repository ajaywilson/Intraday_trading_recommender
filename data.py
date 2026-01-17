import yfinance as yf

def fetch_data(symbol, interval, period):
    return yf.download(symbol, interval=interval, period=period, progress=False)
