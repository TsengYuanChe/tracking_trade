import pandas as pd
import yfinance as yf

CSV_PATH = "signals.csv"

def calculate_profit(csv_path):
    df = pd.read_csv(csv_path)

    results = []

    for _, row in df.iterrows():
        code = str(row["Code"])
        action = row["Action"]
        buy_price = row["Value"]

        if action != "BUY":
            continue

        # yfinance 台股代碼需要加 .TW
        ticker = yf.Ticker(code + ".TW")
        hist = ticker.history(period="1d")

        if hist.empty:
            print(f"⚠ 無法取得 {code} 的價格資料")
            continue

        close_price = hist["Close"].iloc[-1]

        # 百分比
        pct = (close_price - buy_price) / buy_price * 100

        results.append((code, buy_price, close_price, pct))

    return results


if __name__ == "__main__":
    results = calculate_profit(CSV_PATH)

    print("📈 訊號績效:\n")

    total_pct = 0
    win = 0

    for code, buy_price, close_price, pct in results:
        print(f"{code} | BUY: {buy_price} | CLOSE: {close_price:.2f} | Profit: {pct:.2f}%")

        total_pct += pct
        if pct > 0:
            win += 1

    if results:
        avg_pct = total_pct / len(results)
        win_rate = win / len(results) * 100
        print("\n==============================")
        print(f"平均報酬：{avg_pct:.2f}%")
        print(f"勝率：{win_rate:.2f}%")
        print("==============================")
    else:
        print("沒有 BUY 訊號")