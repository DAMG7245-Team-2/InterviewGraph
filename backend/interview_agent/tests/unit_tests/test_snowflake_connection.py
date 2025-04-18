import asyncio
import os

from interview_agent.util import (
    AvailableCategories,
    AvailableDifficulties,
    aget_randomized_interview_questions,
    get_interview_questions,
)

import pytest
from sqlalchemy import text
from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine
from dotenv import load_dotenv


@pytest.fixture
def create_snowflake_engine():
    load_dotenv()
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
    return engine


def test_snowflake_connection_sync(create_snowflake_engine):
    assert create_snowflake_engine is not None
    conn = create_snowflake_engine.connect()
    assert conn is not None
    result = conn.execute(text("SELECT 1"))
    assert result.fetchone()[0] == 1
    conn.close()


@pytest.mark.asyncio
async def test_snowflake_connection_async(create_snowflake_engine):
    def execute_query_sync():
        assert create_snowflake_engine is not None
        conn = create_snowflake_engine.connect()
        assert conn is not None
        result = conn.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1
        conn.close()

    await asyncio.to_thread(execute_query_sync)


def test_get_interview_questions(create_snowflake_engine):
    questions = get_interview_questions(
        create_snowflake_engine,
        AvailableCategories.ALGORITHMS,
        AvailableDifficulties.EASY,
    )
    print(questions[:10])
    assert len(questions) > 0


@pytest.mark.asyncio
async def test_get_interview_questions_async(create_snowflake_engine):
    questions = await aget_randomized_interview_questions(
        create_snowflake_engine,
        AvailableCategories.ALGORITHMS,
        AvailableDifficulties.EASY,
        10,
    )
    assert len(questions) == 10
