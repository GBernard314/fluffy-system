import requests, time
import os
from minio import Minio

API_URL = "https://api.example.com/data"
BUCKET = os.environ["MINIO_BUCKET"]

MINIO_ACCESS_KEY = os.environ['MINIO_ACCESS_KEY']
MINIO_SECRET_KEY = os.environ['MINIO_SECRET_KEY']

MINIO_URL = os.environ.get("MINIO_ENDPOINT", "minio-service:9000")


def wait_for_minio(timeout=60, interval=3):
    start = time.time()
    while True:
        try:
            r = requests.get(MINIO_URL)
            if r.status_code < 500:
                print("MinIO is up!")
                break
        except Exception as e:
            print(f"Waiting for MinIO... ({e})")
        if time.time() - start > timeout:
            print("Timed out waiting for MinIO.")
            exit(1)
        time.sleep(interval)


client = Minio(
    MINIO_URL,
    access_key= MINIO_ACCESS_KEY,
    secret_key= MINIO_SECRET_KEY,
    secure=False  # Set to True if using HTTPS
)

def init_bucket():
    try:
        buckets = client.list_buckets()
        if len(buckets) == 0:
            print("No buckets found. Creating the new bucket...")
            client.make_bucket(BUCKET)
        else:
            print(f"Bucket '{BUCKET}' already exists.")
    except Exception as e:
        print(f"Error creating bucket: {e}")


def main():
    print(f"Connecting to MinIO at {MINIO_URL} with bucket {BUCKET}")
    wait_for_minio()
    init_bucket()
    while True:
        print("Main loop running...")
        time.sleep(10)

if __name__ == "__main__":
    main()