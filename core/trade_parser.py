import pandas as pd
from datetime import datetime, timedelta
from .utils import calc_avg_cost
from .price import get_close_price
from .company import get_company_name

TODAY = datetime.today().strftime("%Y-%m-%d")
YESTERDAY = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
VALID_SELL_DATES = {TODAY, YESTERDAY}

# --------------------------------------------------------
# 統一處理價格的函式
# --------------------------------------------------------
def resolve_price(code, value):
    """
    若 value=null → 用收盤價
    若 value 有數字 → 用該數字
    """
    v = str(value).strip().lower()

    if v in ["null", "", "none"]:
        close_price, _ = get_close_price(code)
        return close_price

    try:
        return float(value)
    except:
        return None

def process_trades(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()

    positions = {}
    completed = []

    for _, row in df.iterrows():
        date = row["date"]
        code = str(row["code"]).strip()
        action = str(row["action"]).strip().lower()
        value = str(row["value"]).strip()

        if code not in positions:
            positions[code] = {"buys": []}

        pos = positions[code]

        # --------------------------------------------------------
        # BUY
        # --------------------------------------------------------
        if action == "buy":
            price = resolve_price(code, value)
            if price is not None:
                pos["buys"].append({"date": date, "price": price})
            continue

        # --------------------------------------------------------
        # KEEP → 用收盤價買進
        # --------------------------------------------------------
        if action == "keep":
            price = resolve_price(code, value)
            if price is not None:
                pos["buys"].append({"date": date, "price": price})
            continue
        
        # --------------------------------------------------------
        # SELL / REDUCE（含 null → 用收盤價）
        # --------------------------------------------------------
        if action in ["sell", "reduce"]:
            if len(pos["buys"]) == 0:
                continue
            
            price = resolve_price(code, value)
            if price is not None:
                continue

            avg_cost = calc_avg_cost(pos["buys"])
            pct = ((price - avg_cost) / avg_cost) * 100

            # SELL 僅在合法日期記錄；REDUCE 全記錄
            if date in VALID_SELL_DATES or action == "reduce":
                completed.append({
                    "code": code,
                    "company": get_company_name(code),
                    "buy_detail": pos["buys"].copy(),
                    "sell_date": date,
                    "avg_cost": avg_cost,
                    "sell_price": price,
                    "pct": pct
                })

            # 賣出後清空，重新計算新的持倉
            positions[code]["buys"] = []

            continue

    # --------------------------------------------------------
    # Open positions
    # --------------------------------------------------------
    open_positions = []
    for code, pos in positions.items():
        if len(pos["buys"]) == 0:
            continue

        close_price, symbol = get_close_price(code)
        if close_price is None:
            continue

        avg_cost = calc_avg_cost(pos["buys"])
        pct = ((close_price - avg_cost) / avg_cost) * 100

        open_positions.append({
            "code": code,
            "company": get_company_name(code),
            "symbol": symbol,
            "buy_detail": pos["buys"],
            "avg_cost": avg_cost,
            "close_price": close_price,
            "pct": pct
        })

    return completed, open_positions