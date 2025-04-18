import os
from fastmcp import FastMCP
from interview_agent.util import (
    AvailableCategories,
    AvailableDifficulties,
    aget_randomized_interview_questions,
)
from sqlalchemy import create_engine
from snowflake.sqlalchemy import URL
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("SQL Agent")


@mcp.add_tool
async def sql_tool(
    category: AvailableCategories = AvailableCategories.ALGORITHMS,
    difficulty: AvailableDifficulties = AvailableDifficulties.MEDIUM,
    num_questions: int = 5,
) -> list[tuple[str, str]]:
    """Get a list of interview questions and their expected answers from the database
    Args:
        category: The category of the questions to retrieve
        difficulty: The difficulty level of the questions to retrieve
        num_questions: The number of questions to retrieve
    Returns:
        A list of tuples, each containing a question and its expected answer
    """
    engine = create_engine(
        URL(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            role=os.getenv("SNOWFLAKE_ROLE"),
        )
    )
    return await aget_randomized_interview_questions(
        engine, category, difficulty, num_questions
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
