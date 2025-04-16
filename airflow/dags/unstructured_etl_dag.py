from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import boto3
import re
import requests
import os
from io import StringIO

from dotenv import load_dotenv
import pandas as pd
import re
import json
import boto3
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from io import BytesIO

# === Config ===
BUCKET = "interview-prep-ak"
INPUT_KEY = "original_md/interviewQA_README.md"
OUTPUT_PREFIX = "webscrapemarkdownfiles"
TOPICS = ["DevOps", "Algorithms", "Data structures", "Networks"]
REGION = "us-east-1"  # update if needed

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

PROMPT_TEMPLATE = """
You are a technical interviewer.

Given this markdown content about "{category}", extract high-quality interview-style **questions and answers** in JSON format.

Output format:
[
  {{
    "Question": "...",
    "Answer": "...",
    "Category": "{category}",
    "Difficulty": "Easy/Medium/Hard"
  }}
]
Markdown:
{text}
"""
prompt_template = PromptTemplate.from_template(PROMPT_TEMPLATE)

def delete_s3_folder(bucket, prefix):
    s3 = boto3.client("s3")
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    if "Contents" in response:
        print(f"Found {len(response['Contents'])} objects. Deleting...")

        objects_to_delete = [{"Key": obj["Key"]} for obj in response["Contents"]]

        # Batch delete (max 1000 objects per request)
        s3.delete_objects(Bucket=bucket, Delete={"Objects": objects_to_delete})

        print(f"Deleted objects under s3://{bucket}/{prefix}")
    else:
        print(f"No objects found in s3://{bucket}/{prefix}")

# === Helper Functions ===

def read_markdown_from_s3(**kwargs):
    s3 = boto3.client('s3', region_name=REGION)
    response = s3.get_object(Bucket=BUCKET, Key=INPUT_KEY)
    content = response['Body'].read().decode('utf-8')
    kwargs['ti'].xcom_push(key='markdown', value=content)

def extract_and_scrape(**kwargs):
    md_content = kwargs['ti'].xcom_pull(key='markdown', task_ids='read_markdown')
    s3 = boto3.client('s3', region_name=REGION)
    delete_s3_folder("interview-prep-ak", "webscrapedmarkdownfiles")

    for topic in TOPICS:
        # Extract section under ## {topic}
        pattern = rf"## {re.escape(topic)}\s+(.*?)(?=\n## |\Z)"
        match = re.search(pattern, md_content, re.DOTALL)
        if not match:
            continue
        section = match.group(1)
        links = re.findall(r'\* \[(.*?)\]\((http.*?)\)', section)

        for title, url in links:
            try:
                print(f"Scraping: {title} -> {url}")
                jina_url = f"https://r.jina.ai/{url}"
                resp = requests.get(jina_url, timeout=15)
                resp.raise_for_status()
                markdown_text = resp.text
            except Exception as e:
                markdown_text = f"Error fetching {url} via Jina: {e}"

            # Save to S3
            filename = f"{OUTPUT_PREFIX}/{title.replace('/', '-')}.md"
            s3.put_object(
                Bucket=BUCKET,
                Key=filename,
                Body=markdown_text.encode('utf-8'),
                ContentType='text/markdown'
            )
            print(f"Uploaded: s3://{BUCKET}/{filename}")

def chunk_markdown(text, chunk_size=3000, chunk_overlap=500):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def safe_parse_json_blocks(text):
    try:
        match = re.search(r'\[\s*{.*?}\s*]', text, re.DOTALL)
        return json.loads(match.group()) if match else []
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        return []

def extract_qa_from_chunks(category, markdown_text):
    chunks = chunk_markdown(markdown_text)
    all_qa = []
    for i, chunk in enumerate(chunks):
        try:
            message = HumanMessage(content=prompt_template.format(category=category, text=chunk))
            response = llm([message])
            parsed = safe_parse_json_blocks(response.content)
            all_qa.extend(parsed)
        except Exception as e:
            print(f"LLM error on chunk {i}: {e}")
            continue
    return all_qa

def process_markdown_and_generate_csv(**kwargs):
    s3 = boto3.client("s3", region_name=REGION)
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{OUTPUT_PREFIX}/")
    delete_s3_folder("interview-prep-ak", "QA-csvfiles")

    all_rows = []

    for obj in response.get("Contents", []):
        key = obj["Key"]
        if not key.endswith(".md"):
            continue

        filename = os.path.basename(key)
        category = filename.split("_")[0]

        body = s3.get_object(Bucket=BUCKET, Key=key)['Body'].read().decode("utf-8")
        qas = extract_qa_from_chunks(category, body)
        all_rows.extend(qas)

    df = pd.DataFrame(all_rows, columns=["Question", "Answer", "Category", "Difficulty"])
    
    # Save CSV to memory and upload
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    s3.put_object(
        Bucket=BUCKET,
        Key="QA-csvfiles/interview_qa_dataset.csv",
        Body=buffer,
        ContentType="text/csv"
    )
    print(" Q&A CSV saved to s3://interview-prep-ak/QA-csvfiles/interview_qa_dataset.csv")



# === 1. Validate CSV in S3 ===
def validate_qa_csv_from_s3(**kwargs):
    s3 = boto3.client("s3", region_name=REGION)
    obj = s3.get_object(Bucket=BUCKET, Key="QA-csvfiles/interview_qa_dataset.csv")
    df = pd.read_csv(BytesIO(obj['Body'].read()))

    log_stream = StringIO()
    log = lambda msg: log_stream.write(msg + '\n')

    log(" Validating structure...")
    expected_cols = ['Question', 'Answer', 'Category', 'Difficulty']
    if list(df.columns) != expected_cols:
        log(" Columns are not correct")
    else:
        log(" Column names are correct.")

    log("\n Checking for missing values...")
    log(str(df.isnull().sum()))

    log("\n Validating Difficulty values...")
    allowed = {"Easy", "Medium", "Hard"}
    invalid = df[~df["Difficulty"].isin(allowed)]
    if not invalid.empty:
        log(f" Found {len(invalid)} rows with invalid difficulty values:")
        log(str(invalid[["Question", "Difficulty"]].head()))
    else:
        log(" All difficulty values are valid.")

    log("\n Checking question formatting...")
    no_qmark = df[~df["Question"].str.strip().str.endswith("?")]
    if not no_qmark.empty:
        log(f" Found {len(no_qmark)} questions without '?':")
        log(str(no_qmark[["Question"]].head()))
    else:
        log(" All questions end with '?'")

    log("\n Checking short answers...")
    short = df[df["Answer"].str.len() < 20]
    if not short.empty:
        log(f" Found {len(short)} answers shorter than 20 characters:")
        log(str(short[["Question", "Answer"]].head()))
    else:
        log(" All answers have sufficient length.")

    log("\n Checking for duplicates...")
    dups = df[df.duplicated(subset=["Question"], keep=False)]
    if not dups.empty:
        log(f" Found {dups['Question'].nunique()} unique duplicate questions ({len(dups)} total rows):")
        log(str(dups[["Question", "Answer"]].head()))
    else:
        log(" No duplicate questions found.")

    log("\n Sample of valid data:")
    log(str(df.sample(5)))

    # Create log file with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/log_{timestamp}.txt"

    # Upload to S3
    s3.put_object(
        Bucket="interview-prep-ak",
        Key=log_filename,
        Body=log_stream.getvalue().encode('utf-8'),
        ContentType='text/plain'
    )

    print(f" Validation log uploaded to s3://interview-prep-ak/{log_filename}")



# === 2. Remove Duplicates and Upload Two CSVs to S3 ===
def remove_and_upload_csvs(**kwargs):
    delete_s3_folder("interview-prep-ak", "cleaned")
    delete_s3_folder("interview-prep-ak", "duplicated")
    s3 = boto3.client("s3", region_name=REGION)
    obj = s3.get_object(Bucket=BUCKET, Key="QA-csvfiles/interview_qa_dataset.csv")
    df = pd.read_csv(BytesIO(obj['Body'].read()))

    # Deduplicate
    duplicate_rows = df[df.duplicated(subset=["Question"], keep=False)]
    deduped_df = df.drop_duplicates(subset=["Question"], keep="first")

    # Save to memory
    buffer_deduped = BytesIO()
    buffer_duplicate = BytesIO()
    deduped_df.to_csv(buffer_deduped, index=False)
    duplicate_rows.to_csv(buffer_duplicate, index=False)
    buffer_deduped.seek(0)
    buffer_duplicate.seek(0)

    # Upload both to S3
    s3.put_object(Bucket=BUCKET, Key="cleaned/interview_qa_dataset_deduped.csv", Body=buffer_deduped.getvalue())
    s3.put_object(Bucket=BUCKET, Key="duplicates/check_duplicate.csv", Body=buffer_duplicate.getvalue())

    print(f" Uploaded deduplicated file to s3://{BUCKET}/cleaned/")
    print(f" Uploaded duplicates to s3://{BUCKET}/duplicates/")



# === DAG Definition ===

with DAG(
    dag_id="scrape_markdown_links_dag_v5",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["scraping", "markdown", "JinaAI"],
) as dag:
    

    read_markdown = PythonOperator(
        task_id="read_markdown",
        python_callable=read_markdown_from_s3,
    )

    extract_scrape_save = PythonOperator(
        task_id="extract_scrape_save",
        python_callable=extract_and_scrape,
    )

    generate_qa_csv = PythonOperator(
    task_id="generate_qa_csv",
    python_callable=process_markdown_and_generate_csv,
    )

    validate_qa_csv = PythonOperator(
        task_id="validate_qa_csv",
        python_callable=validate_qa_csv_from_s3,
    )

    deduplicate_csv_and_upload = PythonOperator(
        task_id="deduplicate_csv_and_upload",
        python_callable=remove_and_upload_csvs,
    )

    


    read_markdown >> extract_scrape_save >> generate_qa_csv >> validate_qa_csv >> deduplicate_csv_and_upload

    