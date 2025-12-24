from FinMind.data import DataLoader
from datetime import datetime, timedelta

loader = DataLoader()

def get_close_price(code):
    """
    使用 FinMind 取得最新收盤價
    支援：台股上市 + 上櫃
    """

    today = datetime.today().strftime("%Y-%m-%d")
    start = (datetime.today() - timedelta(days=5)).strftime("%Y-%m-%d")

    try:
        df = loader.taiwan_stock_daily(
            stock_id=str(code),
            start_date=start,
        )

        if df.empty:
            print(f"[FinMind empty] {code}")
            return None, None

        # 取最近一筆有效收盤價
        last_row = df.iloc[-1]
        close_price = float(last_row["close"])

        return close_price, f"{code}.TW"

    except Exception as e:
        print(f"[FinMind Error] {code}: {e}")
        return None, None