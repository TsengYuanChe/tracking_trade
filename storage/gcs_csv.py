from google.cloud import storage
import time

def download_csv_from_gcs(bucket_name, blob_name, local_path):
    print("---------------------------------------------------")
    print(f"[GCS] START download")
    print(f"[GCS] bucket = {bucket_name}")
    print(f"[GCS] blob   = {blob_name}")
    print(f"[GCS] local  = {local_path}")
    print("---------------------------------------------------")

    start = time.time()

    try:
        client = storage.Client()
        print("[GCS] Client created OK")

        bucket = client.bucket(bucket_name)
        print("[GCS] Bucket object OK")

        blob = bucket.blob(blob_name)
        print(f"[GCS] Blob exists? {blob.exists()}")

        if not blob.exists():
            print(f"[ERROR] File not found: gs://{bucket_name}/{blob_name}")
            return False

        print("[GCS] Downloading...")
        blob.download_to_filename(local_path)
        print("[GCS] Download DONE")

        return True

    except Exception as e:
        print(f"[GCS ERROR] {e}")
        return False

    finally:
        print(f"[GCS] Total time: {time.time() - start:.2f} sec")
        print("---------------------------------------------------")