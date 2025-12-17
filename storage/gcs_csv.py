from google.cloud import storage
import time

def download_csv_from_gcs(bucket_name, blob_name, local_path, timeout=5):
    """讀取 GCS，若失敗 5 秒就丟錯誤（避免 Cloud Run Job 卡 10 分鐘）"""

    start = time.time()

    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        print(f"[INFO] Reading GCS: {bucket_name}/{blob_name}")

        # 這裡加 timeout 避免卡住
        with blob.open("rb", timeout=timeout) as f:
            content = f.read()

        with open(local_path, "wb") as f:
            f.write(content)

    except Exception as e:
        elapsed = round(time.time() - start, 2)
        raise Exception(f"GCS 讀取失敗（{elapsed}s）：{e}")


def upload_csv_to_gcs(bucket_name: str, blob_name: str, local_path: str):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.upload_from_filename(local_path)
    print(f"[GCS] Uploaded {local_path} → gs://{bucket_name}/{blob_name}")