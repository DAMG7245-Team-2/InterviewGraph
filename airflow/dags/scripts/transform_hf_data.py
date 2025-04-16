import logging
import os
import sys

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def transform_hf_data(hf_path : str = "./tmp_data/hf_data/information.csv"):
    """
    Transform Hugging Face dataset to standardized format.
    
    Args:
        hf_path: Path to the Hugging Face dataset CSV file
        
    Returns:
        str: Path to the transformed CSV file
    """
    try:
        hf_df = pd.read_csv(hf_path)
        # Remove any unnamed columns
        hf_df.drop(columns=[col for col in hf_df.columns if col.startswith('Unnamed')], inplace=True, errors='ignore')

        # Standardize column names to match our schema
        hf_df = hf_df.rename(columns={
            'language': 'Category',
            ' level ': 'Difficulty', 
            'Questions': 'Question',  
            'Answers': 'Answer'    
        })

        # Select only the columns we need in the correct order
        hf_df = hf_df[['Question', 'Answer', 'Category', 'Difficulty']]
        hf_df.to_csv(hf_path, index=False)
        logger.info("Transformed Hugging Face dataset to standard format")
        return os.path.abspath(hf_path)

    except Exception as e:
        logger.error(f"Error transforming Hugging Face dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    transformed_csv_path = transform_hf_data("./tmp_data/hf_data/interview-questions.csv")
    print(transformed_csv_path)