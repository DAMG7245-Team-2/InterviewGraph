quizzer_prompt = """You are an expert technical quizmaster, your task is to generate {num_questions} quiz questions QAList using the context provided to you:
{context}
Each QA should have question, expected_answer fields."""

feedback_prompt = """You are an expert technical quizzer, You are given the question, expected_answer, given_answer:
{qa}
Based on this information, generate feedback for the user.
The feedback should include a similarity score between the expected answer and the given answer, and a brief explanation of the score. The feedback should be in the format:
"similarity": <similarity_score>, "feedback": <feedback>"""
