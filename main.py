from dotenv import load_dotenv
load_dotenv()

from core.trade_parser import process_trades
from report.formatter import print_report, format_report
from notify.push_bot import push_message

CSV_PATH = "data/trades.csv"

if __name__ == "__main__":
    completed, open_positions = process_trades(CSV_PATH)
    text = format_report(completed, open_positions)
    
    print_report(completed, open_positions)
    push_message(text)
    