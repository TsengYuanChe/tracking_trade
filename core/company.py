import yfinance as yf
import json
import os

DATA_PATH = os.path.join("data", "company_names.json")

# load 台股列表
with open(DATA_PATH, "r", encoding="utf-8") as f:
    COMPANY_NAMES = json.load(f)


def get_company_name(code):
    """
    先從本地 JSON 讀中文名稱，沒有再 fallback 到 Yahoo。
    """
    if code in COMPANY_NAMES:
        return COMPANY_NAMES[code]

    # fallback from Yahoo
    for market in ["TW", "TWO"]:
        try:
            info = yf.Ticker(f"{code}.{market}").get_info()
            name = info.get("longName")
            if name:
                for remove in ["股份有限公司", "有限公司", "股份有限", "有線公司"]:
                    name = name.replace(remove, "")
                return name.strip()
        except:
            continue

    return None