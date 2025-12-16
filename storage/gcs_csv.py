from google.cloud import storage

def download_csv_from_gcs(bucket_name: str, blob_name: str, local_path: str):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.download_to_filename(local_path)
    print(f"[GCS] Downloaded gs://{bucket_name}/{blob_name} → {local_path}")


def upload_csv_to_gcs(bucket_name: str, blob_name: str, local_path: str):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.upload_from_filename(local_path)
    print(f"[GCS] Uploaded {local_path} → gs://{bucket_name}/{blob_name}")