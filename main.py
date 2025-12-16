from dotenv import load_dotenv
load_dotenv()

import os
from core.trade_parser import process_trades
from report.formatter import print_report, format_report
from notify.push_bot import push_message

# 新增：如果在 GCP，會使用 gcs_csv 讀取雲端檔案
USE_GCS = os.getenv("USE_GCS", "false").lower() == "true"

if USE_GCS:
    from storage.gcs_csv import download_csv_from_gcs
    CSV_PATH = "/tmp/trades.csv"   # Cloud Run Job 寫入位置
else:
    CSV_PATH = "data/trades.csv"   # 本地環境使用


def load_csv():
    """本地用本地，GCP 用 GCS。"""
    if USE_GCS:
        bucket = os.getenv("GCS_BUCKET")
        blob = os.getenv("GCS_CSV_PATH", "trades.csv")
        print(f"[INFO] Downloading csv from gs://{bucket}/{blob}")
        download_csv_from_gcs(bucket, blob, CSV_PATH)
    else:
        print(f"[INFO] Using local CSV: {CSV_PATH}")


if __name__ == "__main__":
    load_csv()  # 先確保 CSV 正確讀取

    completed, open_positions = process_trades(CSV_PATH)
    text = format_report(completed, open_positions)

    print_report(completed, open_positions)
    push_message(text)