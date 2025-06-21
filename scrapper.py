import websocket, json, io
import os
from minio import Minio
from datetime import datetime, timezone

BUCKET = os.environ["MINIO_BUCKET"]

MINIO_ROOT_USER = os.environ['MINIO_ROOT_USER']
MINIO_ROOT_PASSWORD = os.environ['MINIO_ROOT_PASSWORD']

MINIO_URL = os.environ.get("MINIO_ENDPOINT", "minio-service:9000")

FINNHUB_API_KEY = os.environ['FINNHUB_API_KEY']

minio_client = Minio(
    MINIO_URL,
    access_key= MINIO_ROOT_USER,
    secret_key= MINIO_ROOT_PASSWORD,
    secure=False  # Set to True if using HTTPS
)

def init_bucket():
    try:
        buckets = [b.name for b in minio_client.list_buckets()]
        if BUCKET not in buckets:
            print(f"Bucket '{BUCKET}' not found. Creating the new bucket...")
            minio_client.make_bucket(BUCKET)
        else:
            print(f"Bucket '{BUCKET}' already exists.")
    except Exception as e:
        print(f"Error creating bucket: {e}")

FINNHUB_WS_URL = f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}"

def on_message(ws, message):
    data = json.loads(message)

    bucket_name = BUCKET
    # Rename object using up-to-date datetime to avoid collisions
    now_str = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z") 
    object_name = f"{now_str}_{data.get('data', [{}])[0].get('s', 'None')}_{data.get('type', 'unknown')}.json"
    message_bytes = json.dumps(data).encode("utf-8")

    # Upload the message if it's not a ping message
    if data.get('type') == 'ping':
        print("Received ping message, skipping upload.")
        return
    elif data.get('type') == 'error':
        print(f"Error message received: {data.get('msg')}")
        return
    else:
        minio_client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(message_bytes),
            length=len(message_bytes),
            content_type="application/json"
        )

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    ws.send('{"type":"subscribe","symbol":"WPEA"}')
    ws.send('{"type":"subscribe","symbol":"DCAM"}')
    ws.send('{"type":"subscribe","symbol":"MIWO00000PUS"}')
    ws.send('{"type":"subscribe","symbol":"INX"}')
    ws.send('{"type":"subscribe","symbol":"AAPL"}')
    ws.send('{"type":"subscribe","symbol":"NVDA"}')
    ws.send('{"type":"subscribe","symbol":"MSFT"}')
    ws.send('{"type":"subscribe","symbol":"GOOGL"}')
    ws.send('{"type":"subscribe","symbol":"GOOG"}')
    ws.send('{"type":"subscribe","symbol":"META"}')
    ws.send('{"type":"subscribe","symbol":"AMZN"}')
    ws.send('{"type":"subscribe","symbol":"TSLA"}')
    ws.send('{"type":"subscribe","symbol":"WMT"}')
    ws.send('{"type":"subscribe","symbol":"BINANCE:BTCEUR"}')
    ws.send('{"type":"subscribe","symbol":"BINANCE:XRPEUR"}')


if __name__ == "__main__":
    print(f"Connecting to MinIO at {MINIO_URL} with bucket {BUCKET}")
    init_bucket()
    ws = websocket.WebSocketApp(
        FINNHUB_WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()