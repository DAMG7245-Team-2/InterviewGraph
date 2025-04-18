from fastapi import FastAPI, UploadFile, Form
from services.snowflake_utils import fetch_question
from services.llm_utils import normalize_io_with_llm, review_with_llm
from services.evaluator import run_code_in_sandbox, validate
import os

app = FastAPI()


@app.get("/question/")
def get_question(difficulty: str):
    problem_id, question, test_input, expected_output, solution = fetch_question(difficulty)
    #stdin, stdout = normalize_io_with_llm(question, test_input, expected_output)
    return {
        "problem_id": problem_id,
        "question": question,
        "stdin": test_input,
        "stdout": expected_output,
        "solution": solution,
    }


@app.post("/submit/")
async def submit_code(
    code: UploadFile,
    input: str = Form(...),
    output: str = Form(...),
    question: str = Form(...)
):
    user_code = (await code.read()).decode("utf-8")
    stdin, stdout = normalize_io_with_llm(question, input, output)
    actual_output = run_code_in_sandbox(user_code, stdin)
    result = validate(actual_output, stdout)
    feedback = review_with_llm(question, user_code, stdin, stdout, actual_output)
    return {
        "result": result,
        "actual_output": actual_output,
        "feedback": feedback,
    }

