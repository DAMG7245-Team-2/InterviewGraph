import logging
import os
import shutil
import sys

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def merge_datasets(
    hf_path: str = "./tmp_data/hf_data/information.csv", 
    kaggle_path: str = "./tmp_data/kaggle_data/Software Questions.csv", 
    output_path: str = "./tmp_data/merged_data.csv",
):
    """Merge interview question datasets from Hugging Face and Kaggle sources.
    
    Args:
        hf_path: Path to the Hugging Face dataset CSV file
        kaggle_path: Path to the Kaggle dataset CSV file
        output_path: Path where the merged dataset will be saved

    Returns:
        Path to the merged dataset CSV file
    """
    # Check if input files exist
    if not os.path.exists(hf_path) or not os.path.exists(kaggle_path):
        logger.error(f"One or both of the datasets do not exist at '{hf_path}' or '{kaggle_path}'.")
        sys.exit(1)

    try:
        logger.info(f"Merging datasets from '{hf_path}' and '{kaggle_path}'...")
        hf_df = pd.read_csv(hf_path)
        kaggle_df = pd.read_csv(kaggle_path, encoding='ISO-8859-1')

        # Combine both datasets
        merged_df = pd.concat([hf_df, kaggle_df], ignore_index=True)
        logger.info("Combined both datasets")

        # Save the merged dataset to the output path
        merged_df.to_csv(output_path, index=False)
        logger.info(f"Merged datasets and saved to '{output_path}'.")

        # Clean up intermediate data directories
        try:
            # Remove the directories containing the source files
            shutil.rmtree(os.path.dirname(hf_path))
            shutil.rmtree(os.path.dirname(kaggle_path))
            logger.info(f"Removed intermediate datasets '{hf_path}' and '{kaggle_path}'.")
        except FileNotFoundError as e:
            logger.warning("Directories not found. Skipping deletion.")
        except Exception as e:
            logger.error(f"An error occurred while deleting directories: {e}")

        return os.path.abspath(output_path)

    except Exception as e:
        logger.error(f"An error occurred during dataset merging: {e}")
        sys.exit(1)

if __name__ == "__main__":
    merged_csv_path = merge_datasets(
        hf_path="./tmp_data/hf_data/information.csv",
        kaggle_path="./tmp_data/kaggle_data/Software Questions.csv",
        output_path="./tmp_data/merged_data.csv"
    )
    print(merged_csv_path)