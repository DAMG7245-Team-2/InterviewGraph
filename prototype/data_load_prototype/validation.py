import os
from dotenv import load_dotenv
import pandas as pd
load_dotenv()

def validate_qa_csv(path="interview_qa_dataset.csv"):
    df = pd.read_csv(path)
    
    print(" Validating structure...")
    expected_cols = ['Question', 'Answer', 'Category', 'Difficulty']
    assert list(df.columns) == expected_cols, "Columns are not correct"
    
    print("\n Checking for missing values...")
    print(df.isnull().sum())
    
    print("\n Validating Difficulty values...")
    allowed_difficulties = {"Easy", "Medium", "Hard"}
    invalid = df[~df["Difficulty"].isin(allowed_difficulties)]
    if not invalid.empty:
        print(f" Found {len(invalid)} rows with invalid difficulty values:\n", invalid[["Question", "Difficulty"]].head())

    print("\n Checking question formatting...")
    no_question_mark = df[~df["Question"].str.strip().str.endswith("?")]
    if not no_question_mark.empty:
        print(f" Found {len(no_question_mark)} questions without '?' at the end:\n", no_question_mark[["Question"]].head())

    print("\n Checking short answers...")
    short = df[df["Answer"].str.len() < 20]
    if not short.empty:
        print(f" Found {len(short)} answers shorter than 20 characters:\n", short[["Question", "Answer"]].head())

    print("\n Checking for duplicates...")
    dups = df[df.duplicated(subset=["Question"], keep=False)]
    if not dups.empty:
        unique_dup_count = dups["Question"].nunique()
        total_dup_rows = len(dups)
        print(f" Found {unique_dup_count} unique duplicate questions ({total_dup_rows} total duplicate rows).")
        print(dups[["Question", "Answer"]].head())

    print("\n Sample of valid data:\n", df.sample(5))

# Run the validator


def remove_duplicate_questions(
    input_path="interview_qa_dataset.csv",
    deduped_output_path="interview_qa_dataset_deduped_2.csv",
    duplicate_output_path="check_duplicate.csv"
):
    # Load the dataset
    df = pd.read_csv(input_path)

    # Identify duplicates (all occurrences, not just one)
    duplicate_rows = df[df.duplicated(subset=["Question"], keep=False)]

    # Drop duplicates to get unique questions
    deduped_df = df.drop_duplicates(subset=["Question"], keep="first")

    # Save deduplicated dataset
    deduped_df.to_csv(deduped_output_path, index=False)

    # Save duplicate entries to a separate file
    duplicate_rows.to_csv(duplicate_output_path, index=False)

    # Report summary
    print(" Deduplication complete.")
    print(f" Original rows: {len(df)}")
    print(f" Deduplicated rows: {len(deduped_df)}")
    print(f" Duplicate rows saved to: {duplicate_output_path}")
    print(f" Cleaned file saved to: {deduped_output_path}")

    return deduped_df, duplicate_rows

import boto3

def upload_files_to_s3(
    files: dict,
    bucket_name: str,
    aws_profile: str = None
):
    """
    files: dict with local_path as key, s3_key as value
    """
    session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
    s3 = session.client("s3")

    for local_path, s3_key in files.items():
        s3.upload_file(local_path, bucket_name, s3_key)
        print(f" Uploaded {local_path} to s3://{bucket_name}/{s3_key}")

# Step 1: Clean and export CSVs
deduped_file, duplicate_file = remove_duplicate_questions(
    input_path="interview_qa_dataset.csv"
)

# Step 2: Upload to S3
upload_files_to_s3(
    files={
        deduped_file: "qa_data/interview_qa_dataset_deduped.csv",
        duplicate_file: "qa_data/check_duplicate.csv"
    },
    bucket_name=os.get,
    
)



# Example usage
validate_qa_csv()

#remove_duplicate_questions()
