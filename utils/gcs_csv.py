import pandas as pd
from google.cloud import storage
import io
import os

BUCKET_NAME = os.getenv("GCS_BUCKET")
CSV_FILE = os.getenv("GCS_CSV_PATH", "trades.csv")

if not BUCKET_NAME:
    print("❌ ERROR: Cloud Run 未設定 GCS_BUCKET！")


def get_gcs_client():
    """建立 GCS Client（預設使用 Cloud Run 的 service account）"""
    return storage.Client()


def read_csv_from_gcs():
    """
    從 GCS 讀取 trades.csv
    若不存在 → 回傳空 DataFrame
    """

    client = get_gcs_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(CSV_FILE)

    if not blob.exists():
        print("⚠ GCS CSV 不存在，建立新空白 CSV...")
        return pd.DataFrame(columns=["date", "code", "action", "value"])

    csv_bytes = blob.download_as_bytes()
    return pd.read_csv(io.BytesIO(csv_bytes))


def write_csv_to_gcs(df: pd.DataFrame):
    """
    將 DataFrame 寫回 GCS (取代原本的 trades.csv)
    """

    client = get_gcs_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(CSV_FILE)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)

    blob.upload_from_string(csv_buffer.getvalue(), content_type="text/csv")
    print(f"✔ CSV 已成功寫回 GCS：gs://{BUCKET_NAME}/{CSV_FILE}")