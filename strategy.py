def check_signal(df, i):
    row = df.iloc[i]
    prev_high = df["High"].iloc[i-11:i-1].max()

    return (
        row["Close"] > row["VWAP"] and
        row["EMA9"] > row["EMA20"] and
        row["Close"] > row["Open"] and
        row["Volume"] > 1.5 * row["Vol_Avg"] and
        row["Close"] > prev_high
    )
