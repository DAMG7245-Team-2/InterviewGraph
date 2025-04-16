from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

# Add your project root (adjust this path as needed in the container!)
sys.path.append('/opt/project/')

from backend.data_load.interview_questions_load import main as load_interview_data

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='load_interview_data_dag',
    default_args=default_args,
    description='DAG to load interview questions data into Snowflake and Pinecone',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['interview', 'data-load'],
) as dag:

    load_data = PythonOperator(
        task_id='load_data_into_snowflake',
        python_callable=load_interview_data
    )

    load_data