#!/usr/bin/env python3
"""
Script to load interview questions data from Hugging Face dataset,
perform data preprocessing, and load it into a Snowflake database table.
"""

import os
import sys
import logging

from dotenv import load_dotenv
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_environment_variables():
    """
    Load environment variables from .env file.
    """
    load_dotenv()
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
        logging.error(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        logging.debug("Please check your .env file or environment settings.")
        sys.exit(1)


def load_and_preprocess_data(file_path):
    """
    Load data from CSV file and perform basic preprocessing.
    
    Args:
        file_path (str): Path to the CSV file.
        
    Returns:
        pandas.DataFrame: Preprocessed dataframe.
    """
    try:
        df = pd.read_csv(file_path)
        # Remove unnamed column
        if 'Unnamed: 5' in df.columns:
            df = df.drop(columns=['Unnamed: 5'])
        # Remove rows with missing values
        df = df.dropna()
        # Reset index
        df = df.reset_index(drop=True)
        return df
    except Exception as e:
        logging.error(f"Error loading or preprocessing data: {e}")
        sys.exit(1)


def connect_to_snowflake():
    """
    Establish connection to Snowflake.
    
    Returns:
        tuple: (connection, cursor) if successful, (None, None) otherwise.
    """
    try:
        conn = snowflake.connector.connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA")
        )
        cursor = conn.cursor()
        logging.info("Connection established successfully.")
        return conn, cursor
    except snowflake.connector.errors.Error as e:
        logging.error(f"Error connecting to Snowflake: {e}")
        return None, None


def upload_data_to_snowflake(conn, df, table_name):
    """
    Upload dataframe to Snowflake table.
    
    Args:
        conn (snowflake.connector.connection): Snowflake connection.
        df (pandas.DataFrame): Dataframe to upload.
        table_name (str): Name of the table to create/update.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        success, nchunks, nrows, _ = write_pandas(
            conn, df, table_name, auto_create_table=True
        )
        logging.info(f"Uploaded {nrows} rows in {nchunks} chunks")
        return success
    except Exception as e:
        logging.error(f"Error uploading data to Snowflake: {e}")
        return False


def close_connection(conn, cursor):
    """
    Close Snowflake connection and cursor.
    
    Args:
        conn (snowflake.connector.connection): Snowflake connection.
        cursor (snowflake.connector.cursor): Snowflake cursor.
    """
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    logging.info("Connection closed.")


def main():
    """
    Main function to orchestrate the data loading process.
    """
    # Load environment variables
    load_environment_variables()
    
    # Load and preprocess data
    file_path = "hf://datasets/Aiman1234/Interview-questions/information.csv"
    df = load_and_preprocess_data(file_path)
    
    # Connect to Snowflake
    conn, cursor = connect_to_snowflake()
    if not conn or not cursor:
        sys.exit(1)
    
    # Upload data to Snowflake
    table_name = "interview_questions"
    success = upload_data_to_snowflake(conn, df, table_name)
    
    close_connection(conn, cursor)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
