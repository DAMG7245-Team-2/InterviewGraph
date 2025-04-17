from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import os

# Constants
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
INDEX_NAME = "resourcebooks1"
S3_BUCKET = "interview-prep-ak"
S3_PREFIX = "books/"
BATCH_SIZE = 1000

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="load_data_pinecone_rag",
    default_args=default_args,
    description="Load markdown files from S3, chunk, embed, and upload to Pinecone",
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    tags=["pinecone", "embedding", "markdown", "s3"],
) as dag:

    def get_files(**context):
        import boto3
        s3_client = boto3.client('s3')
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
        md_files = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".md")]
        context['ti'].xcom_push(key="md_files", value=md_files)

    def chunk_md_files(**context):
        import boto3
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        s3_client = boto3.client('s3')

        def read_markdown_from_s3(bucket, key):
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            return obj["Body"].read().decode("utf-8")

        def chunk_document(text):
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                separators=["\n\n", "\n", ".", "?", "!", " ", ""]
            )
            return splitter.split_text(text)

        md_files = context['ti'].xcom_pull(task_ids="get_md_files", key="md_files")
        all_chunks = {}

        for s3_key in md_files:
            content = read_markdown_from_s3(S3_BUCKET, s3_key)
            if not content:
                continue
            chunks = chunk_document(content)
            all_chunks[s3_key] = chunks

        context['ti'].xcom_push(key="chunked_data", value=all_chunks)

    def embed_chunks(**context):
        from sentence_transformers import SentenceTransformer

        embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        chunked_data = context['ti'].xcom_pull(task_ids="chunk_md_files", key="chunked_data")
        embedded_data = {}

        for file_key, chunks in chunked_data.items():
            embeddings = embedding_model.encode(chunks).tolist()
            embedded_data[file_key] = list(zip(chunks, embeddings))

        context['ti'].xcom_push(key="embedded_data", value=embedded_data)

    def load_to_pinecone(**context):
        from dotenv import load_dotenv
        from pinecone import Pinecone, ServerlessSpec
        import os
        envpath="airflow/.env"
        load_dotenv(envpath)
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

        embedded_data = context['ti'].xcom_pull(task_ids="embed_chunks", key="embedded_data")

        if INDEX_NAME not in pc.list_indexes().names():
            pc.create_index(
                name=INDEX_NAME,
                dimension=384,
                metric='cosine',
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )
        index = pc.Index(INDEX_NAME)

        for s3_key, pairs in embedded_data.items():
            file_base = os.path.basename(s3_key).replace(".md", "")
            try:
                title, author = file_base.split("-")
            except ValueError:
                print(f"Skipping malformed filename: {file_base}")
                continue

            chunk_prefix = f"{title}_{author}"
            vectors = [
                {
                    "id": f"{chunk_prefix}_{i}",
                    "values": embedding,
                    "metadata": {
                        "text": chunk,
                        "title": title,
                        "author": author,
                    }
                }
                for i, (chunk, embedding) in enumerate(pairs)
            ]

            for i in range(0, len(vectors), BATCH_SIZE):
                batch = vectors[i:i + BATCH_SIZE]
                index.upsert(vectors=batch)
                print(f"Uploaded {len(batch)} vectors for {s3_key}")

    # Tasks
    get_files_task = PythonOperator(
        task_id="get_md_files",
        python_callable=get_files,
        provide_context=True,
    )

    chunk_files_task = PythonOperator(
        task_id="chunk_md_files",
        python_callable=chunk_md_files,
        provide_context=True,
    )

    embed_chunks_task = PythonOperator(
        task_id="embed_chunks",
        python_callable=embed_chunks,
        provide_context=True,
    )

    load_to_pinecone_task = PythonOperator(
        task_id="load_to_pinecone",
        python_callable=load_to_pinecone,
        provide_context=True,
    )

    # Dependencies
    get_files_task >> chunk_files_task >> embed_chunks_task >> load_to_pinecone_task
