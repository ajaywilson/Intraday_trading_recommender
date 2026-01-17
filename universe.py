import pandas as pd
import yfinance as yf

def get_universe():
    url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
    df = pd.read_csv(url)
    symbols = [s + ".NS" for s in df["Symbol"].tolist()]

    valid = []

    for sym in symbols:
        try:
            test = yf.download(sym, period="1d", progress=False)
            if not test.empty:
                valid.append(sym)
        except:
            continue

    print(f"Loaded {len(valid)} valid symbols out of {len(symbols)}")
    return valid
