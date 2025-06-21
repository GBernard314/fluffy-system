from pyspark.sql import SparkSession
import os
import boto3
from pyspark.sql import functions as F
import psycopg2

# --- MinIO/S3 config ---
MINIO_ENDPOINT = os.environ["MINIO_ENDPOINT"]
MINIO_ROOT_USER = os.environ["MINIO_ROOT_USER"]
MINIO_ROOT_PASSWORD = os.environ["MINIO_ROOT_PASSWORD"]
MINIO_BUCKET = os.environ["MINIO_BUCKET"]

# --- SQL DB config ---
JDBC_URL = os.environ["POSTGRES_URL"]  # e.g., "jdbc:postgresql://dbhost:5432/mydb"
JDBC_USER = os.environ["POSTGRES_USER"]
JDBC_PASSWORD = os.environ["POSTGRES_PASSWORD"]
JDBC_DRIVER = os.environ.get("POSTGRES_DRIVER", "org.postgresql.Driver")  # Change if using MySQL, etc.


# Parse host, db, port from JDBC_URL
import re
m = re.match(r"jdbc:postgresql://([^:/]+):?(\d+)?/(\w+)", JDBC_URL)
host, port, dbname = m.group(1), m.group(2) or 5432, m.group(3)

conn = psycopg2.connect(
    host=host,
    port=port,
    dbname=dbname,
    user=JDBC_USER,
    password=JDBC_PASSWORD
)
cur = conn.cursor()

# Table name and schema
table_name = "all_trades"
create_sql = """
CREATE TABLE IF NOT EXISTS all_trades (
    c TEXT,
    p DOUBLE PRECISION,
    s TEXT,
    t BIGINT,
    v DOUBLE PRECISION,
    type TEXT
);
"""

# Check and create table if needed
cur.execute(create_sql)
conn.commit()
cur.close()
conn.close()



# Spark session with S3A and JDBC support
spark = SparkSession.builder \
    .appName("MinIO Example") \
    .config("spark.jars", "/jars/hadoop-aws-3.3.4.jar,/jars/aws-java-sdk-bundle-1.12.367.jar,/jars/postgresql-42.7.3.jar") \
    .config("spark.hadoop.fs.s3a.endpoint", f"http://{MINIO_ENDPOINT}") \
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ROOT_USER) \
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_ROOT_PASSWORD) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

# List files in the bucket (using boto3)
s3 = boto3.resource(
    's3',
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ROOT_USER,
    aws_secret_access_key=MINIO_ROOT_PASSWORD,
)

s3_client = boto3.client(
    's3',
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ROOT_USER,
    aws_secret_access_key=MINIO_ROOT_PASSWORD,
)

bucket = s3.Bucket(MINIO_BUCKET)
# Get the 10 earliest objects by LastModified
objects = sorted(bucket.objects.all(), key=lambda obj: obj.last_modified)
for obj in objects:
    key = obj.key
    # Skip already processed files (tagged)
    
    # Get tags
    response = s3_client.get_object_tagging(Bucket=MINIO_BUCKET, Key=key)
    tags = response['TagSet']

    if any(tag['Key'] == 'processed' and tag['Value'] == 'true' for tag in tags):
        continue

    # --- Spark logic: read, process, write ---
    df = spark.read.json(f"s3a://{MINIO_BUCKET}/{key}")
    
    # Explode the 'data' array so each item becomes a row
    df = df.withColumn("data", F.explode("data"))

    # Flatten the fields from 'data' into top-level columns
    data_fields = df.schema["data"].dataType.names
    for field in data_fields:
        df = df.withColumn(field, F.col(f"data.{field}"))

    # Optionally drop the original 'data' column
    df = df.drop("data")
    
    # Store all rows in the database (append mode)
    df.write \
        .format("jdbc") \
        .option("url", JDBC_URL) \
        .option("dbtable", "all_trades") \
        .option("user", JDBC_USER) \
        .option("password", JDBC_PASSWORD) \
        .option("driver", JDBC_DRIVER) \
        .mode("append") \
        .save()


    # Set tags
    s3_client.put_object_tagging(
        Bucket=MINIO_BUCKET,
        Key=key,
        Tagging={'TagSet': [{'Key': 'processed', 'Value': 'true'}]}
    )

spark.stop()