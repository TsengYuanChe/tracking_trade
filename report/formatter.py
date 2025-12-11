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
        
def format_report(completed, open_positions):
    output = []

    wins = 0
    total_trades = len(completed) + len(open_positions)

    output.append("=== COMPLETED TRADES ===")

    if not completed:
        output.append("\n(No recent completed trades)")
    else:
        for t in completed:
            if t["pct"] > 0:
                wins += 1

            output.append(f"\n[{t['code']}] — {t['company']}")
            for b in t["buy_detail"]:
                output.append(f"  BUY  {b['date']} @ {b['price']:.2f}")
            output.append(f"  SELL {t['sell_date']} @ {t['sell_price']:.2f}")
            output.append(f"  P/L  {t['pct']:+.2f}%")

    output.append("\n=== OPEN POSITIONS ===")

    if not open_positions:
        output.append("\n(No open positions)")
    else:
        for pos in open_positions:
            if pos["pct"] > 0:
                wins += 1

            output.append(f"\n[{pos['code']}] — {pos['company']}")
            for b in pos["buy_detail"]:
                output.append(f"  BUY   {b['date']} @ {b['price']:.2f}")
            output.append(f"  CLOSE @ {pos['close_price']:.2f}")
            output.append(f"  P/L   {pos['pct']:+.2f}%")

    # Summary
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    output.append(f"\n=== SUMMARY ===")
    output.append(f"Win Rate: {win_rate:.2f}%")

    return "\n".join(output)