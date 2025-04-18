from e2b_code_interpreter import Sandbox

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

    print("\n Code sent to E2B Sandbox:\n" + "=" * 40)
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
