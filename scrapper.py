import requests

API_URL = "https://api.example.com/data"  # Replace with actual API endpoint
DATALAKE_URL = "http://datalake-service.local/ingest"  # Replace with actual datalake endpoint

def fetch_data():
    response = requests.get(API_URL)
    response.raise_for_status()
    return response.json()

def send_to_datalake(data):
    response = requests.post(DATALAKE_URL, json=data)
    response.raise_for_status()
    return response.json()

def main():
    data = fetch_data()
    result = send_to_datalake(data)
    print("Data sent to datalake:", result)

if __name__ == "__main__":
    main()