"""Define the state structures for the agent."""

from __future__ import annotations
from typing import List, Literal, TypedDict, Annotated
from pydantic import BaseModel, Field
import operator


class Section(BaseModel):
    name: str = Field(description="Name of this section in the report")
    description: str = Field(
        description="Brief description of the concept/skill covered in this section"
    )
    research: bool = Field(
        description="Whether to perform research for this section of the report."
    )
    content: str = Field(description="Content of this section")


class Sections(BaseModel):
    sections: List[Section] = Field(description="List of sections in the report")


class SearchQuery(BaseModel):
    search_query: str = Field(description="Query for web search")


class Queries(BaseModel):
    queries: List[SearchQuery] = Field(description="List of search queries")


class ReportStateInput(TypedDict):
    topic: str


class ReportStateOutput(TypedDict):
    final_report: str


class ReportState(TypedDict):
    topic: str
    sections: List[Section]
    completed_sections: Annotated[list, operator.add]
    report_sections_from_research: str
    final_report: str


class SectionState(TypedDict):
    topic: str
    section: Section
    search_iterations: int
    search_queries: list[SearchQuery]
    source_str: str
    report_sections_from_research: str
    completed_sections: list[Section]


class SectionOutputState(TypedDict):
    completed_sections: list[Section]


class Feedback(BaseModel):
    grade: Literal["pass", "fail"] = Field(
        description="Evaluation result indicating whether the response meets requirements ('pass') or needs revision ('fail')."
    )
    follow_up_queries: list[SearchQuery] = Field(
        description="Follow-up queries to refine the search for more information."
    )


class JobDescriptionValidation(BaseModel):
    valid: Literal["valid", "invalid"] = Field(
        description="Evaluation result indicating whether the job description is valid or not."
    )
