from datetime import datetime
import os
import shutil

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from scripts.clean_data import clean_data
from scripts.download_hf import download_hf_dataset
from scripts.download_kaggle import download_kaggle_dataset
from scripts.load_to_snowflake import load_to_snowflake
from scripts.merge_datasets import merge_datasets
from scripts.transform_hf_data import transform_hf_data
from scripts.transform_kaggle_data import transform_kaggle_data 

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1
}

def delete_tmp_data_folder(folder_path="./tmp_data"):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"Deleted folder: {folder_path}")
    else:
        print(f"Folder not found: {folder_path}")

with DAG(
    dag_id='data_etl_pipeline',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    description="DAG with parallel data download/transform and merged load flow"
) as dag:

    download_kaggle = PythonOperator(
        task_id='download_kaggle',
        python_callable=download_kaggle_dataset
    )

    download_hf = PythonOperator(
        task_id='download_hf',
        python_callable=download_hf_dataset
    )

    transform_kaggle = PythonOperator(
        task_id='transform_kaggle',
        python_callable=transform_kaggle_data
    )

    transform_hf = PythonOperator(
        task_id='transform_hf',
        python_callable=transform_hf_data
    )

    merge = PythonOperator(
        task_id='merge_datasets',
        python_callable=merge_datasets
    )

    clean = PythonOperator(
        task_id='clean_data',
        python_callable=clean_data
    )

    load = PythonOperator(
        task_id='load_to_snowflake',
        python_callable=load_to_snowflake
    )

    cleanup_tmp_data = PythonOperator(
        task_id='cleanup_tmp_data',
        python_callable=delete_tmp_data_folder,
        trigger_rule=TriggerRule.ALL_DONE
    )

    # DAG Flow
    download_kaggle >> transform_kaggle
    download_hf >> transform_hf

    [transform_kaggle, transform_hf] >> merge >> clean >> load >> cleanup_tmp_data