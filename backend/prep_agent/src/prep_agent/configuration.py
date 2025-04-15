"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Optional

from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv

load_dotenv()
MY_REPORT_STRUCTURE = """Use the following structure to generate a interview preparation guide report on user provided job description:

1. Introduction (no research needed)
    - Highlight top technical skills, tools and technologies needed for the job
    - Structured table with 3 columns: Technical skill, Description, Importance (Required, Preferred)

2. Roadmap (no research needed)
    - mermaid markdown code for a flowchart diagram of the recommended roadmap to achieve the preparation for the topic divided into 3 sections (Fundamentals, Intermediate, Advanced)
    - Each node in the diagram should have a name of the concept

3. Main Body Sections (research needed)
    - Each section should focus on a technical concept that is relevant to the job description
    - Each section should serve as a standalone guide to the technical concept/skill
    - Provide at least 1 structured element (either a list or a table) per section that is relevant to the concept/skill discussed in the section
    - Include at least 3 multiple choice questions per section that tests the understanding of the concept/skill discussed in the section

4. Conclusion (no research needed)
    - Aim for 1 structural element that distills the main concepts covered in the main body sections
    - Provide a concise summary of the report"""


@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""

    report_structure: str = MY_REPORT_STRUCTURE
    planner_provider: str = "openai"
    planner_model: str = "o3-mini"
    writer_provider: str = "openai"
    writer_model: str = "gpt-4o-mini"
    search_api: str = "tavily"
    number_of_queries: int = 5
    top_k: int = 2  # pinecone top k results
    score_threshold: float = 0.8
    max_search_depth: int = 2

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        configurable = (config.get("configurable") or {}) if config else {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})
