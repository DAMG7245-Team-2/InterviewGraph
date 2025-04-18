import os
from dotenv import load_dotenv
load_dotenv()
import glob
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm
import json
import re

# 1. Setup the LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    
)

# 2. Read markdown files
def read_markdown_files(folder="scraped_md"):
    files = glob.glob(os.path.join(folder, "*.md"))
    data = []
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            category = os.path.basename(file).split("_")[0]
            data.append((category, content))
    return data

# 3. Prompt template
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

# 4. Safe JSON parsing
def safe_parse_json_blocks(text):
    try:
        match = re.search(r'\[\s*{.*?}\s*]', text, re.DOTALL)
        return json.loads(match.group()) if match else []
    except Exception as e:
        print(f" JSON Parse Error: {e}")
        return []

# 5. Split long markdown into chunks
def chunk_markdown(text, chunk_size=3000, chunk_overlap=500):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

# 6. Extract Q&A from each chunk
def extract_qa_from_chunks(category, markdown_text):
    chunks = chunk_markdown(markdown_text)
    all_qa = []

    for i, chunk in enumerate(chunks):
        message = HumanMessage(content=prompt_template.format(category=category, text=chunk))
        try:
            response = llm([message])
            parsed = safe_parse_json_blocks(response.content)
            all_qa.extend(parsed)
        except Exception as e:
            print(f" LLM error on chunk {i}: {e}")
            continue

    return all_qa

# 7. Main
def main():
    all_data = read_markdown_files("scraped_md")
    all_rows = []

    for category, content in tqdm(all_data, desc="Processing markdown"):
        qas = extract_qa_from_chunks(category, content)
        all_rows.extend(qas)

    df = pd.DataFrame(all_rows, columns=["Question", "Answer", "Category", "Difficulty"])
    df.to_csv("interview_qa_dataset.csv", index=False)
    print("Done! Saved to `interview_qa_dataset.csv`")

if __name__ == "__main__":
    main()
