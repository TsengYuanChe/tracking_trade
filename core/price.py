import yfinance as yf

def get_close_price(code):
    """
    Returns (price, symbol) or (None, None)
    """
    for market in ["TW", "TWO"]:
        ticker = yf.Ticker(f"{code}.{market}")
        hist = ticker.history(period="1d")

        if not hist.empty:
            return hist["Close"].iloc[-1], f"{code}.{market}"

    return None, None