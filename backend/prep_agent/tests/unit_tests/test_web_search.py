import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from prep_agent.graph import search_web
from prep_agent.state import SectionState, Section, SearchQuery

# Mark all tests in this module as asyncio tests
pytestmark = pytest.mark.asyncio


# Sample state for testing
@pytest.fixture
def section_state():
    return SectionState(
        topic="Software Engineer",
        section=Section(
            name="Technical Skills",
            description="Essential technical skills for a software engineer",
            research=True,
            content="",
        ),
        search_iterations=0,
        search_queries=[
            SearchQuery(
                search_query="essential programming languages for software engineers"
            ),
            SearchQuery(search_query="software development best practices"),
        ],
        source_str="",
        report_sections_from_research="",
        completed_sections=[],
    )


# Mock configuration
@pytest.fixture
def config():
    class MockConfig:
        def __init__(self):
            self.max_search_depth = 2
            self.top_k = 5

    return {"config": MockConfig()}


# Test the search_web function with mocked dependencies
@patch("prep_agent.graph.async_search")
@patch("prep_agent.graph.Pinecone")
@patch("prep_agent.graph.HuggingFaceEmbeddings")
@patch("prep_agent.graph.search_pinecone")
async def test_search_web(
    mock_search_pinecone,
    mock_embeddings,
    mock_pinecone,
    mock_async_search,
    section_state,
    config,
):
    # Set up mocks
    mock_async_search.return_value = "Web search results"
    mock_index = MagicMock()
    mock_pinecone.return_value.Index.return_value = mock_index
    mock_embeddings.return_value = MagicMock()
    mock_search_pinecone.return_value = "Pinecone search results"

    # Execute the function
    result = await search_web(section_state, config)

    # Verify the function was called with the expected parameters
    query_list = [query.search_query for query in section_state["search_queries"]]
    mock_async_search.assert_called_once_with(
        query_list, config["config"].max_search_depth
    )
    # mock_search_pinecone.assert_called_once_with(
    #     mock_index, mock_embeddings.return_value, query_list, config["config"].top_k
    # )

    # Verify the results
    assert "source_str" in result
    assert result["source_str"] == "Web search resultsPinecone search results"
    assert result["search_iterations"] == 1


# Run tests when file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
