import pandas as pd
import yfinance as yf

CSV_PATH = "trades.csv"

# --------------------------------------------------------
# 自動判斷市場別：上市(TW) / 上櫃(TWO)
# --------------------------------------------------------
def resolve_market_symbol(code):
    """
    自動判斷該股票是 TW 還是 TWO
    先嘗試 TW，不行再試 TWO
    """
    code = str(code).strip()
    for market in ["TW", "TWO"]:  # 優先嘗試 TW 的原因：大部分股票在 TW
        ticker = yf.Ticker(f"{code}.{market}")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return f"{code}.{market}"
    return None  # TW/TWO 都抓不到 → 可能下市/興櫃/代碼錯誤


# --------------------------------------------------------
# 單純 BUY 訊號績效模型
# --------------------------------------------------------
def calculate_buy_performance(csv_path):
    df = pd.read_csv(csv_path)

    # 清理欄位名稱
    df.columns = df.columns.str.strip().str.lower()

    results = []

    for _, row in df.iterrows():
        code = str(row["code"]).strip()
        action = str(row["action"]).strip().lower()
        value_raw = str(row["value"]).strip()

        if action != "buy":
            continue
        
        if value_raw.lower() == "null":
            continue
        
        buy_price = float(value_raw)

        # 判斷股票所屬市場 (TW / TWO)
        symbol = resolve_market_symbol(code)
        if symbol is None:
            print(f"⚠ 股票 {code} 無法取得市場別（TW/TWO），可能下市或代碼錯誤")
            continue

        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")

        if hist.empty:
            print(f"⚠ 無法取得 {symbol} 的價格資料")
            continue

        close_price = hist["Close"].iloc[-1]
        pct = (close_price - buy_price) / buy_price * 100

        results.append({
            "code": code,
            "symbol": symbol,
            "buy_price": buy_price,
            "close_price": close_price,
            "pct": pct
        })

    return results


# --------------------------------------------------------
# 主程式
# --------------------------------------------------------
if __name__ == "__main__":
    results = calculate_buy_performance(CSV_PATH)

    print("📈 BUY 訊號績效:\n")

    if not results:
        print("沒有 BUY 訊號")
        exit()

    total_pct = 0
    win = 0

    for r in results:
        print(f"{r['code']} ({r['symbol']}) | BUY: {r['buy_price']} | CLOSE: {r['close_price']:.2f} | Profit: {r['pct']:.2f}%")

        total_pct += r["pct"]
        if r["pct"] > 0:
            win += 1

    avg_pct = total_pct / len(results)
    win_rate = (win / len(results)) * 100

    print("\n==============================")
    print(f"平均報酬：{avg_pct:.2f}%")
    print(f"勝率：{win_rate:.2f}%")
    print("==============================")