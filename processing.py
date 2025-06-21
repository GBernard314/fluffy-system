from pyspark.sql import SparkSession
import os
import boto3
from pyspark.sql import functions as F

# --- MinIO/S3 config ---
MINIO_ENDPOINT = os.environ["MINIO_ENDPOINT"]
MINIO_ROOT_USER = os.environ["MINIO_ROOT_USER"]
MINIO_ROOT_PASSWORD = os.environ["MINIO_ROOT_PASSWORD"]
MINIO_BUCKET = os.environ["MINIO_BUCKET"]

# --- SQL DB config ---
JDBC_URL = os.environ["JDBC_URL"]  # e.g., "jdbc:postgresql://dbhost:5432/mydb"
JDBC_USER = os.environ["JDBC_USER"]
JDBC_PASSWORD = os.environ["JDBC_PASSWORD"]
JDBC_DRIVER = os.environ.get("JDBC_DRIVER", "org.postgresql.Driver")  # Change if using MySQL, etc.

# Spark session with S3A and JDBC support
spark = SparkSession.builder \
    .appName("MinIO to SQL Batch Process") \
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

bucket = s3.Bucket(MINIO_BUCKET)
for obj in bucket.objects.all():
    key = obj.key
    # Skip already processed files (tagged)
    tags = s3.Object(MINIO_BUCKET, key).Tagging().tag_set
    if any(tag['Key'] == 'processed' and tag['Value'] == 'true' for tag in tags):
        continue

    # --- Spark logic: read, process, write ---
    df = spark.read.csv(f"s3a://{MINIO_BUCKET}/{key}", header=True)
    # Example logic: add week/year columns
    df = df.withColumn("week", F.weekofyear(F.col("timestamp")))
    df = df.withColumn("year", F.year(F.col("timestamp")))

    # Group by year, week, and symbol, then count rows per group
    grouped = df.groupBy("year", "week", "s").count()

    # Write the result to SQL DB (append mode)
    grouped.write \
        .format("jdbc") \
        .option("url", JDBC_URL) \
        .option("dbtable", "trade_aggregates") \
        .option("user", JDBC_USER) \
        .option("password", JDBC_PASSWORD) \
        .option("driver", JDBC_DRIVER) \
        .mode("append") \
        .save()

    # Tag the file as processed
    s3.Object(MINIO_BUCKET, key).Tagging().put(
        Tagging={'TagSet': [{'Key': 'processed', 'Value': 'true'}]}
    )

spark.stop()