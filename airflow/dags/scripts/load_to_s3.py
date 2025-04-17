import os
import sys
import logging
from datetime import datetime

from dotenv import load_dotenv
import pandas as pd
import boto3

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def upload_to_s3(file_path: str = "./tmp_data/cleaned_data.csv", 
                 bucket_name: str = "interview-prep-ak", 
                 folder: str = "cleaned"):

    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    # Load AWS credentials
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION", "us-east-1")

    if not aws_access_key or not aws_secret_key:
        logger.error("Missing AWS credentials in environment variables.")
        sys.exit(1)

    # Create boto3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )

    # Generate S3 key with timestamp
    filename = os.path.basename(file_path)
    #timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    s3_key = f"{folder}/{filename.replace('.csv', '')}.csv"

    # Upload to S3
    try:
        s3.upload_file(file_path, bucket_name, s3_key)
        logger.info(f"File uploaded to s3://{bucket_name}/{s3_key}")
        return f"s3://{bucket_name}/{s3_key}"
    except Exception as e:
        logger.exception(f"Failed to upload to S3: {e}")
        sys.exit(1)

if __name__ == "__main__":
    s3_uri = upload_to_s3("./tmp_data/cleaned_data.csv", "interview-prep-ak", "cleaned")
    print("Uploaded to:", s3_uri)
