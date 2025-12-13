import requests

def get_close_price(code):
    """
    Cloud Run 專用：使用 Yahoo Chart API
    避免被 TWSE / TPEX / yfinance 封鎖
    """

    # 先試 TWSE 上市 (.TW)
    symbol_tw = f"{code}.TW"
    price = fetch_from_yahoo(symbol_tw)
    if price is not None:
        return price, symbol_tw

    # 再試上櫃 (.TWO)
    symbol_two = f"{code}.TWO"
    price = fetch_from_yahoo(symbol_two)
    if price is not None:
        return price, symbol_two

    print(f"[ERROR] No price found for {code}")
    return None, None


def fetch_from_yahoo(symbol):
    """
    使用 Yahoo v8 Chart API 抓收盤價
    Cloud Run 不會被封鎖
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"

    headers = {
        "User-Agent": "Mozilla/5.0"  # 避免被當 Bot 擋掉
    }

    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()

        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]

        # 找到最後一筆有效價格
        for c in reversed(closes):
            if c is not None:
                return float(c)

    except Exception as e:
        print(f"Yahoo fetch failed for {symbol}: {e}")

    return None