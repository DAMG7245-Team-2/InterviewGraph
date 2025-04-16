from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from datetime import datetime
import os
from dotenv import load_dotenv

# Load AWS credentials
load_dotenv()
aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
assert aws_access_key_id and aws_secret_access_key, "Missing AWS credentials"

SNOWFLAKE_CONN_ID = "snowflake_default"
STRUCTURED_STAGE_NAME = "structured_interview_stage"
UNSTRUCTURED_STAGE_NAME = "unstructured_interview_stage"

with DAG(
    dag_id="load_csv_to_snowflake_from_s3",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    schedule_interval=None,
    tags=["snowflake", "s3", "csv"],
) as dag:

    # create_database_and_schema_if_not_exists
    create_db_and_schema = SnowflakeOperator(
        task_id="create_database_and_schema_if_not_exists",
        sql="""
        CREATE DATABASE IF NOT EXISTS INTERVIEW_PREP;
        CREATE SCHEMA IF NOT EXISTS INTERVIEW_PREP.QUESTION_ANSWER;
        """,
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
)


    # Create Structured Stage
    create_stage_structured = SnowflakeOperator(
        task_id="create_structured_stage",
        sql=f"""
        CREATE OR REPLACE STAGE {STRUCTURED_STAGE_NAME}
        URL = 's3://interview-prep-ak/cleaned/cleaned_data.csv'
        CREDENTIALS = (
            AWS_KEY_ID = '{aws_access_key_id}'
            AWS_SECRET_KEY = '{aws_secret_access_key}'
        );
        """,
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
    )

    # Create Unstructured Stage
    create_stage_unstructured = SnowflakeOperator(
        task_id="create_unstructured_stage",
        sql=f"""
        CREATE OR REPLACE STAGE {UNSTRUCTURED_STAGE_NAME}
        URL = 's3://interview-prep-ak/cleaned/interview_qa_dataset_deduped.csv'
        CREDENTIALS = (
            AWS_KEY_ID = '{aws_access_key_id}'
            AWS_SECRET_KEY = '{aws_secret_access_key}'
        );
        """,
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
    )

    # Create the target table
    create_table = SnowflakeOperator(
        task_id="create_interview_table",
        sql="""
        CREATE OR REPLACE TABLE interview_questions (
            Question TEXT,
            Answer TEXT,
            Category TEXT,
            Difficulty TEXT
        );
        """,
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
    )

    # Load structured data
    load_structured = SnowflakeOperator(
        task_id="load_structured_csv",
        sql=f"""
        COPY INTO interview_questions
        FROM @{STRUCTURED_STAGE_NAME}
        FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1);
        """,
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
    )

    # Load unstructured data
    load_unstructured = SnowflakeOperator(
        task_id="load_unstructured_csv",
        sql=f"""
        COPY INTO interview_questions
        FROM @{UNSTRUCTURED_STAGE_NAME}
        FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1);
        """,
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
    )

    # Define DAG dependencies
    create_db_and_schema >> [create_stage_structured, create_stage_unstructured] >> create_table >> load_structured >> load_unstructured
