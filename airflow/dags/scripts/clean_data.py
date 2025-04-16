import logging
import os

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def clean_data(input_path: str = "./tmp_data/merged_data.csv"):
    """
    Clean the data by removing rows with missing values.

    Args:
        input_path (str): Path to the merged input CSV file.
    
    Returns:
        str: Path to the cleaned output CSV file.
    """
    try:
        logger.info(f"Loading data from '{input_path}' for cleaning...")
        df = pd.read_csv(input_path)     
        original_shape = df.shape

        # Remove rows with missing values
        logger.info("Removing rows with missing values...")
        df.dropna(inplace=True)

        # Remove duplicate rows
        logger.info("Removing duplicate rows...")
        df.drop_duplicates(inplace=True)
        cleaned_shape = df.shape

        # Remove the old CSV file
        logger.info("Removing the old CSV file...")
        os.remove(input_path)

        # Save the cleaned data to a new CSV file
        output_path = os.path.join(os.path.dirname(input_path), "cleaned_data.csv")
        df.to_csv(output_path, index=False)
        logger.info(f"Cleaned data from {original_shape} to {cleaned_shape} and saved to '{output_path}'.")
        return os.path.abspath(output_path)

    except Exception as e:
        logger.error(f"An error occurred during data cleaning: {e}")

if __name__ == "__main__":
    final_csv_path = clean_data("./tmp_data/merged_data.csv")
    print(final_csv_path)