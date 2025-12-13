import requests
import json

def get_close_price(code):
    """
    改用台灣證交所 + 上櫃中心 API
    Cloud Run 100% 可用
    """

    # --- 1. TWSE (上市) ---
    try:
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={code}.tw"
        res = requests.get(url, timeout=5)
        data = res.json()

        if "msgArray" in data and len(data["msgArray"]) > 0:
            item = data["msgArray"][0]
            price = float(item.get("z", 0))  # 當前成交價
            if price > 0:
                return price, f"{code}.TW"
    except Exception as e:
        print(f"TWSE fetch failed: {e}")

    # --- 2. TPEX (上櫃) ---
    try:
        url = f"https://www.tpex.org.tw/webstockapi/getStockInfo?stock={code}"
        res = requests.get(url, timeout=5)
        js = res.json()

        if "msgArray" in js and len(js["msgArray"]) > 0:
            item = js["msgArray"][0]
            price = float(item.get("z", 0))
            if price > 0:
                return price, f"{code}.TWO"
    except Exception as e:
        print(f"TPEX fetch failed: {e}")

    print(f"[ERROR] No price found for {code}")
    return None, None