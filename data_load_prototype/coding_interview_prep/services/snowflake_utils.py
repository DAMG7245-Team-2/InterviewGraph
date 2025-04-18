import os
import snowflake.connector
from dotenv import load_dotenv
from typing import Tuple
from pathlib import Path
current_dir = Path(__file__).parent.parent
env_path = current_dir / '.env'

if not env_path.exists():
    print(f"Error: .env file not found at {env_path}")
    print("Current working directory:", os.getcwd())
    print("Directory contents:", os.listdir(current_dir))
else:
    print("Found .env file")
    load_dotenv(dotenv_path=env_path, override=True)

conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
)

def fetch_question(difficulty: str) -> Tuple[str, str, str, str, str]:
    table = "CODING_QUESTIONS_TEST"
    cur = conn.cursor()
    query = f"""
        SELECT "problem_id", "question", "solutions", "input_output", "difficulty", 
               "url", "starter_code", "Test_Input", "Expected_Output"
        FROM {table}
        WHERE "difficulty" = %s
          AND "starter_code" = 'nan'
          AND "Test_Input" IS NOT NULL
          AND "Expected_Output" IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 1
    """
    cur.execute(query, (difficulty,))
    row = cur.fetchone()
    if not row:
        raise Exception("No matching questions found.")
    return row[0], row[1], row[7], row[8], row[2]
