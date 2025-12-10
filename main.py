from core.trade_parser import process_trades
from report.formatter import print_report

CSV_PATH = "data/trades.csv"

if __name__ == "__main__":
    completed, open_positions = process_trades(CSV_PATH)
    print_report(completed, open_positions)