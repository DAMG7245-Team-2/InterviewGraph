import pytest
from unittest.mock import MagicMock
from interview_agent.util import (
    get_interview_questions,
    AvailableCategories,
    AvailableDifficulties,
)


@pytest.fixture
def mock_engine():
    """Fixture to create a mock SQLAlchemy engine."""
    mock_engine = MagicMock()  # Use MagicMock to handle magic methods
    mock_conn = MagicMock()  # Use MagicMock to handle magic methods
    mock_engine.connect.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    return mock_engine, mock_conn


def test_get_interview_questions_success(mock_engine):
    """Test successful retrieval of interview questions."""
    mock_engine, mock_conn = mock_engine

    # Setup mock results
    expected_results = [
        (
            "What is a binary search tree?",
            "A binary search tree is a data structure...",
        ),
        ("What is the time complexity of binary search?", "O(log n)"),
    ]
    mock_conn.execute.return_value.fetchall.return_value = expected_results

    # Call the function
    result = get_interview_questions(
        engine=mock_engine,
        category=AvailableCategories.ALGORITHMS,
        difficulty=AvailableDifficulties.MEDIUM,
    )

    # Verify the function was called correctly
    mock_conn.execute.assert_called_once()
    call_args = mock_conn.execute.call_args[0][0]
    assert (
        str(call_args)
        == "SELECT Question, Answer FROM interview_questions WHERE category = 'Algorithms' AND difficulty = 'Medium'"
    )
    mock_conn.execute.return_value.fetchall.assert_called_once()

    # Verify the result
    assert result == expected_results


def test_get_interview_questions_empty_result(mock_engine):
    """Test when no questions are found."""
    mock_engine, mock_conn = mock_engine

    # Setup mock empty results
    mock_conn.execute.return_value.fetchall.return_value = []

    # Call the function
    result = get_interview_questions(
        engine=mock_engine,
        category=AvailableCategories.NETWORKS,
        difficulty=AvailableDifficulties.HARD,
    )

    # Verify the result is empty
    assert result == []


def test_get_interview_questions_all_categories_and_difficulties(mock_engine):
    """Test with all available categories and difficulties."""
    mock_engine, mock_conn = mock_engine

    # Setup mock results
    sample_result = [("Sample Question", "Sample Answer")]
    mock_conn.execute.return_value.fetchall.return_value = sample_result

    # Test all combinations of categories and difficulties
    for category in AvailableCategories:
        for difficulty in AvailableDifficulties:
            result = get_interview_questions(
                engine=mock_engine, category=category, difficulty=difficulty
            )
            assert result == sample_result

            # Verify the correct SQL query was generated
            mock_conn.execute.assert_called()
            call_args = mock_conn.execute.call_args[0][0]
            assert (
                str(call_args)
                == f"SELECT Question, Answer FROM interview_questions WHERE category = '{category.value}' AND difficulty = '{difficulty.value}'"
            )
