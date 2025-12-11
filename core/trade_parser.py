import pandas as pd
from datetime import datetime, timedelta
from .utils import calc_avg_cost
from .price import get_close_price
from .company import get_company_name

TODAY = datetime.today().strftime("%Y-%m-%d")
YESTERDAY = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

VALID_SELL_DATES = {TODAY, YESTERDAY}

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

        if value.lower() == "null":
            continue

        price = float(value)

        if code not in positions:
            positions[code] = {"buys": []}

        pos = positions[code]

        # BUY
        if action == "buy":
            pos["buys"].append({"date": date, "price": price})

        # SELL / REDUCE
        if action in ["sell", "reduce"]:
            if len(pos["buys"]) == 0:
                continue

            avg_cost = calc_avg_cost(pos["buys"])
            pct = ((price - avg_cost) / avg_cost) * 100

            if date in VALID_SELL_DATES:
                completed.append({
                    "code": code,
                    "company": get_company_name(code),
                    "buy_detail": pos["buys"].copy(),
                    "sell_date": date,
                    "avg_cost": avg_cost,
                    "sell_price": price,
                    "pct": pct
                })

            positions[code]["buys"] = []

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