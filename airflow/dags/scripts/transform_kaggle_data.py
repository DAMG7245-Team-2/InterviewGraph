import logging
import os
import sys

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def transform_kaggle_data(kaggle_path : str = "./tmp_data/kaggle_data/Software Questions.csv"):
    """
    Transform Kaggle dataset to standardized format.
    
    Args:
        kaggle_path: Path to the Kaggle dataset CSV file

    Returns:
        str: Path to the transformed CSV file
    """

    try:
        kaggle_df = pd.read_csv(kaggle_path, encoding='ISO-8859-1')
        # Standardize column names to match our schema
        kaggle_df = kaggle_df.rename(columns={
            'Question': 'Question',
            'Answer': 'Answer',
            'Category': 'Category',
            'Difficulty': 'Difficulty'
        })

        # Select only the columns we need in the correct order
        kaggle_df = kaggle_df[['Question', 'Answer', 'Category', 'Difficulty']]
        kaggle_df.to_csv(kaggle_path, index=False)
        logger.info("Transformed Kaggle dataset to standard format")
        return os.path.abspath(kaggle_path)

    except Exception as e:
        logger.error(f"Error transforming Kaggle dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    transformed_csv_path = transform_kaggle_data("./tmp_data/kaggle_data/Software Questions.csv")
    print(transformed_csv_path)