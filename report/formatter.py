def print_report(completed, open_positions):
    wins = 0
    total_trades = len(completed) + len(open_positions)

    print("\n==================== COMPLETED TRADES ====================\n")

    for t in completed:
        if t["pct"] > 0:
            wins += 1

        print(f"[{t['code']}] — {t['company'] or 'Unknown Company'}")
        print("  Buy Details:")
        for b in t["buy_detail"]:
            print(f"    {b['date']} → {b['price']:.2f}")

        print(f"  Sell Date   : {t['sell_date']}")
        print(f"  Avg Cost    : {t['avg_cost']:.2f}")
        print(f"  Sell Price  : {t['sell_price']:.2f}")
        print(f"  P/L (%)     : {t['pct']:+.2f}%")
        print("------------------------------------------------------------")

    print("\n==================== OPEN POSITIONS ====================\n")

    for pos in open_positions:
        if pos["pct"] > 0:
            wins += 1

        print(f"[{pos['code']}] — {pos['company'] or 'Unknown Company'}")
        print("  Buy Details:")
        for b in pos["buy_detail"]:
            print(f"    {b['date']} → {b['price']:.2f}")

        print(f"  Avg Cost    : {pos['avg_cost']:.2f}")
        print(f"  Close Price : {pos['close_price']:.2f}")
        print(f"  P/L (%)     : {pos['pct']:+.2f}%")
        print("------------------------------------------------------------")

    print("\n==================== SUMMARY ====================\n")
    if total_trades > 0:
        print(f"Win Rate: {(wins / total_trades) * 100:.2f}%")
    else:
        print("No trades found.")