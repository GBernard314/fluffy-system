# Fluffy System: Spark Data Pipeline with MinIO and PostgreSQL
[![wakatime](https://wakatime.com/badge/github/GBernard314/fluffy-system.svg)](https://wakatime.com/@Azarogue/projects/mglllgawlh?start=2025-06-19&end=2025-06-22)
## Overview

This project implements a data processing pipeline using PySpark, MinIO (S3-compatible object storage), and PostgreSQL, all orchestrated on Kubernetes.  
It reads JSON data from MinIO, processes it with Spark, and writes results to a PostgreSQL database.  
All components are containerized and configured for cloud-native deployment.

---

## Prerequisites

- NFS server for persistent storage (for PostgreSQL and the datalake)
```bash
sudo apt install nfs-common -y
```
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed and configured
```bash
sudo snap install kubectl --classic
```
- Docker (for building images)
```bash
sudo snap install docker
```
- Access to a container registry (optional, for pushing images, as of now, everythign is locally hosted)

- Ready to use NFS Shares on your server (1 for the Datalake and one for the DB)
```bash
mkdir -p /yourmountpointforpv
chmod 777 /yourmountpointforpv # dangerous, maybe adequate user / permissions are required
```
---

## Project Structure

```bash
.
├── k3s/
│   ├── minio.yaml            # MinIO Deployment, Service, and PVC
│   ├── postgres.yaml         # PostgreSQL Deployment, Service, and PVC
│   ├── processing.yaml       # Spark processing Job/CronJob
│   ├── pv.yaml               # Creation of PV and PVC for NFS Shares
│   └── scrapper.yaml         # Python scrapping deployment
├── Dockerfile.processing     # Dockerfile for the Spark processing job
├── Dockerfile.scrapper       # Dockerfile for the scrapping job
├── processing.py             # Main PySpark processing script
├── scrapper.py               # Main Python scrapper script (Finnhub.io)
├── requirements.txt          # Python dependencies for the scrapper, for processing it's self contained
├── icon.png          
└── README.md
```

---

## Setup & Deployment

### 1. **Clone the Repository**

```bash
git clone https://github.com/GBernard314/fluffy-system
cd fluffy-system
```

### 2. **Create the Persistent Volumes and Claims**

Edit `k3s/pv.yaml` to fit your NFS shares on your server.

```bash
kubectl apply -f k3s/pv.yaml
```

### 3. **Configure Secrets**

Edit `k3s/creds.env` and add your MinIO and PostgreSQL credentials.  
**Do not commit real credentials to version control!**

Create the secret:
```bash
kubectl create secret generic fluffy-system-creds --from-env-file=k3s/creds.env
```

### 4. **Deploy PostgreSQL**

```bash
kubectl apply -f k3s/postgres.yaml
```

### 5. **Deploy MinIO**

```bash
kubectl apply -f k3s/minio.yaml
```

### 6. **Build and Push the Scrapper Docker Image**

(Optional) If you want to monitor different stocks you can go in ```scrapper.py``` and look for this part of code and do what you must : 
```python
def on_open(ws):
    ws.send('{"type":"subscribe","symbol":"WPEA"}')
    ws.send('{"type":"subscribe","symbol":"DCAM"}')
    ws.send('{"type":"subscribe","symbol":"MIWO00000PUS"}')
    ws.send('{"type":"subscribe","symbol":"AAPL"}')
    ws.send('{"type":"subscribe","symbol":"BINANCE:BTCEUR"}')
    ws.send('{"type":"subscribe","symbol":"BINANCE:XRPEUR"}')
```

Then build the image:
```bash
docker build -f Dockerfile.scrapper -t my-scrapper:latest .
docker save -o my-scrapper.tar my-scrapper:latest
k3s ctr images import my-scrapper.tar
```


### 7. **Deploy the Scrapper Deployment**

Apply the deployment:
```bash
kubectl apply -f k3s/scrapper.yaml
```

### 8. **Build and Push the Processing Docker Image**

Build the image:
```bash
docker build -f Dockerfile.processing -t my-processing:latest .
docker save -o my-processing.tar my-processing:latest
k3s ctr images import my-processing.tar
```

### 9. **Deploy the Processing Job or CronJob**

(Optional) Adapt the cron schedule at your will (refer to [crontab.guru](https://crontab.guru))


Apply scheduled cronJob:
```bash
kubectl apply -f k3s/processing.yaml
```

---

## Usage

- The scrapper job is connected to the websocket of Finnhub.io and write continuously to the MinIO datalake.
- The processing job will read from MinIO, process the data, and write results to PostgreSQL, on a daily basis according to cron in ```k3s/processing.yaml```.
- You can query results in PostgreSQL using `psql` or any SQL client.

---

## Troubleshooting

- **Permissions errors with PostgreSQL on NFS:**  
  Ensure your NFS export uses `no_root_squash` and the data directory is owned by UID 999.
- **Cannot connect to MinIO or PostgreSQL:**  
  Check service endpoints and credentials in your creds.env and YAML files.
- **Job fails with missing JARs:**  
  Make sure your Dockerfile downloads the correct Hadoop AWS and JDBC driver JARs.

---

## Security Notes

- **Never commit real credentials** to version control.
- Use Kubernetes secrets for all sensitive data.
- Restrict NFS and MinIO access to trusted networks.

---

## License

MIT

---

## Author

Guillaume BERNARD  
guillaume.bernard31415@gmail.com
