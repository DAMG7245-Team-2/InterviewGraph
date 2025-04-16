import logging
import os
import sys

from dotenv import load_dotenv
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def ensure_database_and_schema_exist(conn, database, schema):
    """
    Ensures that the specified database and schema exist in Snowflake.
    If they don't, creates them.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
            cur.execute(f"USE DATABASE {database}")
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        logger.info(f"Database '{database}' and schema '{schema}' created/verified.")
    except snowflake.connector.errors.Error as e:
        logger.exception(f"Error creating/verifying database and schema: {e}")
        sys.exit(1)

def load_to_snowflake(file_path: str = "./tmp_data/cleaned_data.csv", table_name: str = "INTERVIEW_QUESTIONS"):
    logger.info(f"Starting Snowflake data load process for file: {file_path}")

    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    # Load the CSV file into a DataFrame
    try:
        df = pd.read_csv(file_path)
        logger.info(f"File loaded successfully with shape {df.shape}")
    except Exception as e:
        logger.exception(f"Error reading the file: {e}")
        sys.exit(1)

    # Validate required environment variables
    required_vars = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE",
        "SNOWFLAKE_SCHEMA"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    # Connect to Snowflake
    try:
        conn = snowflake.connector.connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA")
        )
        logger.info("Connection to Snowflake established.")
        # Ensure the database and schema exist
        ensure_database_and_schema_exist(conn, os.getenv("SNOWFLAKE_DATABASE"), os.getenv("SNOWFLAKE_SCHEMA"))
    except snowflake.connector.errors.Error as e:
        logger.exception(f"Failed to connect to Snowflake: {e}")
        sys.exit(1)

    # Upload the DataFrame
    try:
        with conn.cursor():
            success, nchunks, nrows, _ = write_pandas(
                conn, 
                df, 
                table_name, 
                auto_create_table=True, 
                overwrite=True
            )
            if success:
                logger.info(f"Successfully uploaded {nrows} rows in {nchunks} chunks to '{table_name}'.")
            else:
                logger.error("Upload failed.")
                sys.exit(1)
    except Exception as e:
        logger.exception(f"Error during upload to Snowflake: {e}")
        sys.exit(1)
    finally:
        conn.close()
        logger.info("Snowflake connection closed.")

    logger.info("Data load process completed successfully.")

if __name__ == "__main__":
    load_to_snowflake("./tmp_data/cleaned_data.csv", "INTERVIEW_QUESTIONS")