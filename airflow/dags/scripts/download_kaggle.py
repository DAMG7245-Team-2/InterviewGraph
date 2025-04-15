import logging
import os
import sys

import kaggle

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_kaggle_dataset(dataset_name = "syedmharis/software-engineering-interview-questions-dataset", output_path = "./tmp_data/kaggle_data"):
    """
    Download Kaggle dataset.

    Args:
        dataset_name: Name of the Kaggle dataset
        output_path: Path where the dataset will be saved

    Returns:
        str: Path to the saved CSV file
    """   
    os.environ['KAGGLE_CONFIG_DIR'] = '/opt/airflow/config' 
    logger.info(f"Authernticating with Kaggle API using config at {os.environ['KAGGLE_CONFIG_DIR']}")
    kaggle.api.authenticate()

    logger.info(f"Downloading Kaggle dataset '{dataset_name}' to '{output_path}'")
    kaggle.api.dataset_download_files(dataset=dataset_name, path=output_path, unzip=True)
    if (os.path.exists(output_path + "/Software Questions.csv")):
        logger.info(f"Dataset downloaded and extracted to '{output_path}'")
        return os.path.abspath(output_path + "/Software Questions.csv")
    else:
        logger.error(f"Dataset download failed.")
        sys.exit(1)

if __name__ == "__main__":
    csv_path = download_kaggle_dataset()
    print(csv_path)