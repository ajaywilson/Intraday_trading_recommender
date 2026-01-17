def check_signal(df, i):
    row = df.iloc[i]

    close = float(row["Close"])
    open_ = float(row["Open"])
    vwap = float(row["VWAP"])
    ema9 = float(row["EMA9"])
    ema20 = float(row["EMA20"])
    volume = float(row["Volume"])
    vol_avg = float(row["Vol_Avg"])

    prev_high = float(df["High"].iloc[i-11:i-1].max())

    return (
        close > vwap and
        ema9 > ema20 and
        close > open_ and
        volume > 1.5 * vol_avg and
        close > prev_high
    )
