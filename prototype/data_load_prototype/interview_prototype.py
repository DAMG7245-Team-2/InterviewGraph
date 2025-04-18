from dotenv import load_dotenv
load_dotenv()

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Initialize models
#question_generator = ChatOpenAI(model="gpt-4", temperature=0.7)
answer_reviewer = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.3)

# Static list of mock questions or you could make this dynamic
technical_questions = [
    "What is the difference between a process and a thread? When would you use multithreading over multiprocessing?",
    "Explain how a hash table works. What are collisions and how are they handled?",
    "What is a memory leak and how can you prevent it in a long-running Python application?",
    "Describe the CAP theorem. How does it affect distributed system design?",
    "What is the time complexity of common operations in a binary search tree, and how does it change for balanced vs unbalanced trees?",
    "How does garbage collection work in Java or Python?",
    "What are the pros and cons of using microservices vs monolithic architecture?",
    "How does an operating system schedule tasks? Explain any one scheduling algorithm in detail.",
    "What is the difference between REST and gRPC APIs? When would you use one over the other?",
    "How does a load balancer work, and why is it important in scalable system design?"
]

# Grading prompt template
grading_prompt_template = ChatPromptTemplate.from_template("""
You are a professional technical interviewer helping a candidate prepare for an interview, Now you are conducting a mock interview. A candidate was asked the following question:

**Question:** {question}

**Candidate's Answer:** {answer}

Evaluate the technical correctness, clarity, and depth. Then provide structured feedback:
- Score: X/10
- Strengths:
- Areas for Improvement:
- Summary Feedback:
""")

# Function to conduct the mock interview
def run_mock_interview():
    for i, question in enumerate(technical_questions, 1):
        print(f"\nQ{i}: {question}")
        user_answer = input("Your answer: ")

        # Prepare grading prompt
        grading_prompt = grading_prompt_template.format_messages(
            question=question,
            answer=user_answer
        )

        # Grade the answer
        review = answer_reviewer(grading_prompt)
        print("\n Feedback:")
        print(review.content)

# Run the agent
if __name__ == "__main__":
    run_mock_interview()
