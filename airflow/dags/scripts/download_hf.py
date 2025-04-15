import logging
import os
import sys

from datasets import load_dataset
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def download_hf_dataset(dataset_name = "Aiman1234/Interview-questions", output_path = "./tmp_data/hf_data"):
    """
    Download Hugging Face dataset and save all splits to a single CSV file.

    Args:
        dataset_name (str): Name of the Hugging Face dataset.
        output_path (str): Path to save the CSV file.

    Returns:
        str: Path to the saved CSV file.
    """
    try:
        logger.info(f"Downloading Hugging Face dataset '{dataset_name}'")
        dataset = load_dataset(dataset_name)

        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)

        # Initialize an empty list to store all dataframes
        all_dfs = []

        # Handle DatasetDict by processing each split
        for split_name, split_data in dataset.items():
            # Convert to pandas DataFrame
            df = split_data.to_pandas()

            # Add to our list of dataframes
            all_dfs.append(df)
            logger.info(f"Processed {split_name} split with {len(df)} rows")

        # Combine all dataframes
        combined_df = pd.concat(all_dfs, ignore_index=True)

        # Save to a single CSV file
        output_file = os.path.join(output_path, "interview-questions.csv")
        combined_df.to_csv(output_file, index=False)
        logger.info(f"Saved all splits ({len(combined_df)} rows total) to '{output_file}'")
        return os.path.abspath(output_file)

    except Exception as e:
        logger.error(f"An error occurred during dataset downloading: {e}")
        sys.exit(1)


if __name__ == "__main__":
    csv_path = download_hf_dataset()
    print(csv_path)