import pandas as pd

def get_universe():
    url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
    df = pd.read_csv(url)
    return [s + ".NS" for s in df["Symbol"].tolist()]
