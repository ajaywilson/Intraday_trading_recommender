def add_indicators(df):
    df["EMA9"] = df["Close"].ewm(span=9).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()

    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    df["VWAP"] = (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()

    df["Vol_Avg"] = df["Volume"].rolling(20).mean()
    return df
