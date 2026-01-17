import yfinance as yf

def fetch_data(symbol, interval, period):
    df = yf.download(symbol, interval=interval, period=period, progress=False)

    # Fix MultiIndex columns returned by yfinance in some environments
    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)

    return df
