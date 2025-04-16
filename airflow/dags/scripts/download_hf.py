import logging
import os
import sys
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_hf_dataset(hf_url="hf://datasets/Aiman1234/Interview-questions/information.csv", output_path="./tmp_data/hf_data"):
    """
    Downloads a CSV file from Hugging Face via fsspec and saves it locally.

    Args:
        hf_url (str): The Hugging Face fsspec-style URL to the CSV.
        output_path (str): Local directory to save the CSV.

    Returns:
        str: Absolute path to the saved CSV file.
    """
    try:
        logger.info(f"Reading CSV from Hugging Face: {hf_url}")

        # Read the CSV directly from Hugging Face
        df = pd.read_csv(hf_url)

        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Save it locally
        output_file = os.path.join(output_path, "information.csv")
        df.to_csv(output_file, index=False)

        logger.info(f"Saved CSV to: {output_file}")
        return os.path.abspath(output_file)

    except Exception as e:
        logger.error(f"Error downloading CSV from Hugging Face: {e}")
        raise

if __name__ == "__main__":
    path = download_hf_dataset()
    print(f"CSV saved at: {path}")


