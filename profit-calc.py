import pandas as pd
import yfinance as yf

CSV_PATH = "trades.csv"

def get_close_price(code):
    for market in ["TW", "TWO"]:
        ticker = yf.Ticker(f"{code}.{market}")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return hist["Close"].iloc[-1], f"{code}.{market}"
    return None, None


def calc_avg_cost(buys):
    return sum(b["price"] for b in buys) / len(buys)


def process_trades(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()

    positions = {}
    completed = []

    for _, row in df.iterrows():
        date = row["date"]
        code = str(row["code"]).strip()
        action = str(row["action"]).strip().lower()
        value_raw = str(row["value"]).strip()

        if value_raw.lower() == "null":
            continue

        price = float(value_raw)

        if code not in positions:
            positions[code] = {"buys": []}

        pos = positions[code]

        if action == "buy":
            pos["buys"].append({"date": date, "price": price})

        if action in ["sell", "reduce"]:
            if len(pos["buys"]) == 0:
                continue

            avg_cost = calc_avg_cost(pos["buys"])
            pct = ((price - avg_cost) / avg_cost) * 100

            completed.append({
                "code": code,
                "buy_dates": [b["date"] for b in pos["buys"]],
                "buy_detail": pos["buys"].copy(),
                "sell_date": date,
                "avg_cost": avg_cost,
                "sell_price": price,
                "pct": pct
            })

            positions[code]["buys"] = []

    # Open positions
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
            "symbol": symbol,
            "buy_dates": [b["date"] for b in pos["buys"]],
            "buy_detail": pos["buys"].copy(),
            "avg_cost": avg_cost,
            "close_price": close_price,
            "pct": pct
        })

    return completed, open_positions


# --------------------------------------------------------
# English Output Formatting + Win Rate
# --------------------------------------------------------
def print_report(completed, open_positions):

    wins = 0
    total_trades = len(completed) + len(open_positions)

    print("\n==================== COMPLETED TRADES ====================\n")

    if not completed:
        print("No completed trades.")
    else:
        for t in completed:
            if t["pct"] > 0:
                wins += 1

            print(f"[{t['code']}]")
            print("  Buy Details :")
            for b in t["buy_detail"]:
                print(f"    {b['date']} → {b['price']:.2f}")

            print(f"  Sell Date   : {t['sell_date']}")
            print(f"  Avg Cost    : {t['avg_cost']:.2f}")
            print(f"  Sell Price  : {t['sell_price']:.2f}")
            print(f"  P/L (%)     : {t['pct']:+.2f}%")
            print("------------------------------------------------------------")

    print("\n==================== OPEN POSITIONS ====================\n")

    if not open_positions:
        print("No open positions.")
    else:
        for pos in open_positions:
            if pos["pct"] > 0:
                wins += 1

            print(f"[{pos['code']}]")
            print("  Buy Details :")
            for b in pos["buy_detail"]:
                print(f"    {b['date']} → {b['price']:.2f}")

            print(f"  Avg Cost    : {pos['avg_cost']:.2f}")
            print(f"  Close Price : {pos['close_price']:.2f}")
            print(f"  P/L (%)     : {pos['pct']:+.2f}%")
            print("------------------------------------------------------------")

    print("\n==================== SUMMARY ====================\n")
    if total_trades > 0:
        win_rate = (wins / total_trades) * 100
        print(f"Win Rate: {win_rate:.2f}%")
    else:
        print("No trades found.")


# --------------------------------------------------------
# Main
# --------------------------------------------------------
if __name__ == "__main__":
    completed, open_positions = process_trades(CSV_PATH)
    print_report(completed, open_positions)