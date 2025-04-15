from prep_agent.graph import is_valid_job_description, search_web
from prep_agent.state import ReportState, SearchQuery, Section, SectionState


# def test_is_valid_job_description():
#     state: ReportState = {
#         "topic": "who is the CEO of Apple?",
#         "sections": [],
#         "completed_sections": [],
#         "report_sections_from_research": "",
#         "final_report": "",
#     }

#     result = is_valid_job_description(state, config)
#     assert result is not None


# def test_web_search():
#     state: SectionState = {
#         "topic": "test",
#         "section": Section(name="test", description="test", research=True, content=""),
#         "search_iterations": 0,
#         "search_queries": [SearchQuery(search_query="test")],
#         "source_str": "",
#         "report_sections_from_research": "",
#         "completed_sections": [],
#     }
#     config =
#     result = search_web(state, )
#     assert result is not None
