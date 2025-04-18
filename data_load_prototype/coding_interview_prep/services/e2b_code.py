import os
import json
import snowflake.connector
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox
from openai import OpenAI
from typing import Tuple
from pathlib import Path

# === Load .env ===
current_dir = Path(__file__).parent.parent
env_path = current_dir / '.env'

if not env_path.exists():
    print(f"Error: .env file not found at {env_path}")
    print("Current working directory:", os.getcwd())
    print("Directory contents:", os.listdir(current_dir))
else:
    print(f"Found .env file at {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)

# === Setup Keys ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
E2B_API_KEY = os.getenv("E2B_API_KEY")
assert OPENAI_API_KEY and E2B_API_KEY, "Missing keys"
client = OpenAI(api_key=OPENAI_API_KEY)

# === Snowflake Config ===
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_TABLE = "CODING_QUESTIONS_TEST"

print("Environment Variables Loaded:")
print(f"SNOWFLAKE_ACCOUNT: {SNOWFLAKE_ACCOUNT}")
print(f"SNOWFLAKE_USER: {SNOWFLAKE_USER}")
print(f"SNOWFLAKE_DATABASE: {SNOWFLAKE_DATABASE}")
print(f"E2B_API_KEY exists: {bool(E2B_API_KEY)}")
print(f"OPENAI_API_KEY exists: {bool(OPENAI_API_KEY)}")

# === Connect to Snowflake ===
conn = snowflake.connector.connect(
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    account=SNOWFLAKE_ACCOUNT,
    warehouse=SNOWFLAKE_WAREHOUSE,
    database=SNOWFLAKE_DATABASE,
    schema=SNOWFLAKE_SCHEMA,
)

# === Fetch question ===
def fetch_question(difficulty: str) -> Tuple[str, str, str, str, str]:
    cur = conn.cursor()
    query = f"""
        SELECT "problem_id", "question", "solutions", "input_output", "difficulty", 
               "url", "starter_code", "Test_Input", "Expected_Output"
        FROM {SNOWFLAKE_TABLE}
        WHERE "difficulty" = %s
          AND "starter_code" = 'nan'
          AND "Test_Input" IS NOT NULL
          AND "Expected_Output" IS NOT NULL
          order by random()
        LIMIT 1
    """
    cur.execute(query, (difficulty,))
    row = cur.fetchone()
    if not row:
        raise Exception("No matching questions found.")
    return row[0], row[1], row[7], row[8], row[2]  # problem_id, question, test_input, expected_output, solution

# === Use LLM to normalize input/output ===
def normalize_io_with_llm(question: str, raw_input: str, raw_output: str) -> Tuple[str, str]:
    
    prompt = f"""
        You are a Python coding assistant. Given a coding question and its associated test input and expected output,
your task is to reformat them to work properly in a stdin/stdout environment, such as a code sandbox.

- Reformat the test input to match exactly what the code's `input()` function expects.
  If the code uses `for _ in range(int(input())):`, then the first line of the input should be an integer.
- Use '\\n' to separate multiple lines as if each call to `input()` reads one line.
- Reformat the expected output as a string as it would be printed via print statements.
- Do NOT add any explanation, just return the output in the following JSON format:

{{
  "stdin": "...",
  "stdout": "..."
}}

Now do this for the following:

Question:
{question}

Raw Test Input:
{raw_input}

Raw Expected Output:
{raw_output}
"""



    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are a helpful Python tutor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
    )

    try:
        parsed = json.loads(response.choices[0].message.content)
        return parsed["stdin"], parsed["stdout"]
    except Exception as e:
        print(" Failed to parse LLM response. Raw output:")
        print(response.choices[0].message.content)
        raise e

# === Run code in sandbox ===
def run_code_in_sandbox(user_code: str, test_input: str) -> str:
    sandbox = Sandbox()

    code = f'''
input_data = """{test_input}"""
input_lines = input_data.strip().split('\\n')
def input():
    return input_lines.pop(0)

import sys
from io import StringIO
sys.stdin = StringIO(input_data)

{user_code}
'''

    print("\n🔧 Code sent to E2B Sandbox:\n" + "=" * 40)
    print(code)
    print("=" * 40)

    result = sandbox.run_code(code)
    sandbox.kill()

    print("\n Sandbox Execution Logs:")
    print("stdout:", result.logs.stdout)
    print("stderr:", result.logs.stderr)
    print("error:", result.error)

    output = "\n".join(result.logs.stdout).strip() if isinstance(result.logs.stdout, list) else str(result.logs.stdout).strip()
    return output



def validate(output: str, expected: str) -> str:
    def normalize(text: str):
        return [line.strip() for line in text.strip().splitlines() if line.strip() != ""]

    actual_lines = normalize(output)
    expected_lines = normalize(expected)

    if actual_lines == expected_lines:
        return " Pass"
    else:
        print("\n🔍 Diff:")
        for i, (a, b) in enumerate(zip(actual_lines, expected_lines)):
            if a != b:
                print(f"Line {i+1}: Expected: '{b}' | Got: '{a}'")
        if len(actual_lines) != len(expected_lines):
            print(f"Line count mismatch: Expected {len(expected_lines)} lines, got {len(actual_lines)}")
        return " Fail"


# === LLM feedback ===
def review_with_llm(question: str, user_code: str, input: str, expected: str, actual: str) -> str:
    prompt = f"""
You're an expert coding interviewer. Review the user's solution.

Question:
{question}

Code:
{user_code}

Test Input:
{input}

Expected Output:
{expected}

Actual Output:
{actual}

Please:
- Point out mistakes or inefficiencies
- Suggest improvements
- Offer encouragement if it mostly works

Respond in a constructive, helpful tone.
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful Python tutor."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()

# === Main ===
if __name__ == "__main__":
    print("Welcome to the Coding Interview Agent ")
    difficulty = input("Select difficulty (introductory/practice/interview): ").strip().lower()

    problem_id, question, test_input, expected_output, solution = fetch_question(difficulty)

    print("\n problem_id:", problem_id)
    print("\n Question:")
    print(question)

    print("\n Reformatting input/output via LLM...")
    test_input, expected_output = normalize_io_with_llm(question, test_input, expected_output)

    print("\n Reformatted Input example:\n", test_input)
    print(" Reformatted Expected output:\n", expected_output)

    code_path = input("\n Enter path to your Python solution file (e.g. solution.py): ").strip()
    code_file = Path(code_path).expanduser().resolve()

    if not code_file.exists():
        raise FileNotFoundError(f" File not found at: {code_file}")

    with open(code_file, "r") as f:
        user_code = f.read()

    actual_output = run_code_in_sandbox(user_code, test_input)
    result = validate(actual_output, expected_output)

    print("\n Result:", result)
    print(" Output:\n", actual_output)

    feedback = review_with_llm(question, user_code, test_input, expected_output, actual_output)
    print("\n Feedback:\n", feedback)
