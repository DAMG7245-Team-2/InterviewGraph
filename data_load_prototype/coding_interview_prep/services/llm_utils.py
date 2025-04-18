import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def normalize_io_with_llm(question: str, raw_input: str, raw_output: str):
    prompt = f"""
    You are a Python coding assistant. Given a coding question and its associated test input and expected output,
    your task is to reformat them to work properly in a stdin/stdout environment...

    Question:
    {question}

    Raw Test Input:
    {raw_input}

    Raw Expected Output:
    {raw_output}

    Return output as:
    {{
      "stdin": "...",
      "stdout": "..."
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are a helpful Python tutor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
    )

    raw_content = response.choices[0].message.content
    print(" Raw LLM output:\n", raw_content)  # <-- Add this line for debugging

    try:
        parsed = json.loads(raw_content)
        return parsed["stdin"], parsed["stdout"]
    except Exception as e:
        print(" Failed to parse JSON. Full content:")
        print(raw_content)
        raise e


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
-When the expected output is different from the actual output, do the following:
    - Point out mistakes or inefficiencies
    - Suggest improvements
    - Offer encouragement if it mostly works

Respond in a constructive, helpful tone.
-When expected output matches the actual output, congratulate the condidate in 1-2 lines
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful Python tutor."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()
