import asyncio
import os
from typing import Literal

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, Send
from pinecone import Pinecone

from prep_agent.configuration import Configuration
from prep_agent.state import (
    JobDescriptionValidation,
    ReportState,
    SectionState,
    SectionOutputState,
    ReportStateInput,
    ReportStateOutput,
    Queries,
    Sections,
    Feedback,
)
from prep_agent.prompts import (
    report_planner_query_writer_instructions,
    report_planner_instructions,
    query_writer_instructions,
    section_writer_inputs,
    section_writer_instructions,
    section_grader_instructions,
    final_section_writer_instructions,
    introduction_section_task,
    introduction_section_quality_checks,
    roadmap_section_task,
    roadmap_section_quality_checks,
    conclusion_section_task,
    conclusion_section_quality_checks,
)
from prep_agent.utils import async_search, format_sections, search_pinecone


load_dotenv()


async def is_valid_job_description(
    state: ReportState, config: RunnableConfig
) -> Command[Literal["planning_node", END]]:
    """Validate the input of the report."""
    my_config = Configuration.from_runnable_config(config)
    job_description = state["topic"]
    writer_provider = my_config.writer_provider
    writer_model_name = my_config.writer_model
    writer_model = init_chat_model(
        model_provider=writer_provider, model=writer_model_name
    )
    structured_llm = writer_model.with_structured_output(JobDescriptionValidation)
    system_instructions = "You are a job description validator. You will be given a text and you will need to validate if it is a valid job description. If the job description is not valid, you will return 'invalid'. If the job description is valid, you will return 'valid'."
    messages = [
        SystemMessage(content=system_instructions),
        HumanMessage(content=job_description),
    ]
    results = await structured_llm.ainvoke(messages)
    print("Job description validation results: ", results)
    if results.valid == "valid":
        return Command(goto="planning_node")
    else:
        return Command(
            goto=END,
            update={
                "final_report": "Invalid job description. Please provide a valid job description."
            },
        )


async def planning_node(state: ReportState, config: RunnableConfig):
    """Generate the initial report sections based on the job description.
    Get the config for report structure
    Generates search queries to gather context for planning
    Performs web searches using the search queries
    Uses an LLM to generate a structured plan with sections

    Args:
        state: The current state of the report.
        config: The configuration for the runnable.

    Returns:
       Dict containing the generated sections.
    """
    topic = state["topic"]
    myconfig = Configuration.from_runnable_config(config)
    report_structure = myconfig.report_structure
    num_queries = myconfig.number_of_queries

    if isinstance(report_structure, dict):
        report_structure = str(report_structure)

    writer_provider = myconfig.writer_provider
    writer_model_name = myconfig.writer_model
    writer_model = init_chat_model(
        model_provider=writer_provider, model=writer_model_name
    )
    structured_llm = writer_model.with_structured_output(Queries)
    system_instructions = report_planner_query_writer_instructions.format(
        topic=topic,
        report_organization=report_structure,
        number_of_queries=num_queries,
    )
    messages = [
        SystemMessage(content=system_instructions),
        HumanMessage(
            content="Generate search queries that will help with planning a comprehensive interview preparation guide report."
        ),
    ]
    results = await structured_llm.ainvoke(messages)
    query_list = [query.search_query for query in results.queries]
    source_str = await async_search(query_list, 2)
    sections_system_instructions = report_planner_instructions.format(
        topic=topic,
        report_organization=report_structure,
        context=source_str,
    )

    planner_provider = myconfig.planner_provider
    planner_model_name = myconfig.planner_model
    planner_message = """Generate the sections of the interview preparation guide report. Your response must include Introduction, Roadmap, at least 8 main body sections with each 'sections' field containing a list of sections, Conclusion. 
                        Each section must have: name, description, plan, research, and content fields."""
    planner_model = init_chat_model(
        model_provider=planner_provider, model=planner_model_name
    )
    structured_planner_llm = planner_model.with_structured_output(Sections)
    messages = [
        SystemMessage(content=sections_system_instructions),
        HumanMessage(content=planner_message),
    ]
    report_sections = await structured_planner_llm.ainvoke(messages)
    sections = report_sections.sections
    return {"sections": sections}


async def section_generate_query(state: SectionState, config: RunnableConfig):
    """Generate search queries for researching a specific section.

    This node uses an LLM to generate targeted search queries based on the
    section topic and description.

    Args:
        state: Current state containing section details
        config: Configuration including number of queries to generate

    Returns:
        Dict containing the generated search queries
    """

    # Get state
    topic = state["topic"]
    section = state["section"]

    # Get configuration
    my_config = Configuration.from_runnable_config(config)
    num_queries = my_config.number_of_queries

    # Generate queries
    writer_provider = my_config.writer_provider
    writer_model_name = my_config.writer_model
    writer_model = init_chat_model(
        model=writer_model_name, model_provider=writer_provider
    )
    structured_llm = writer_model.with_structured_output(Queries)

    # Format system instructions
    system_instructions = query_writer_instructions.format(
        topic=topic, section_topic=section.description, number_of_queries=num_queries
    )

    # Generate queries
    queries = await structured_llm.ainvoke(
        [
            SystemMessage(content=system_instructions),
            HumanMessage(content="Generate search queries on the provided topic."),
        ]
    )

    return {"search_queries": queries.queries}


def map_section_generation(
    state: ReportState, config: RunnableConfig
) -> Command[Literal["generate_sections"]]:
    topic = state["topic"]
    sections = state["sections"]
    sections_str = "\n\n".join(
        f"Section: {section.name}\n"
        f"Description: {section.description}\n"
        f"Research needed: {'Yes' if section.research else 'No'}\n"
        for section in sections
    )
    return Command(
        goto=[
            Send(
                "generate_sections",
                {"topic": topic, "section": s, "search_iterations": 0},
            )
            for s in sections
            if s.research
        ]
    )


async def search_web(state: SectionState, config: RunnableConfig):
    """Search the web for information related to the section.

    Args:
        state: Current state containing section details
        config: Configuration including search depth

    Returns:
        Dict containing the search results
    """

    # Get state
    query_list = [query.search_query for query in state["search_queries"]]

    # Get configuration
    my_config = Configuration.from_runnable_config(config)
    max_search_depth = my_config.max_search_depth
    top_k = my_config.top_k
    score_threshold = my_config.score_threshold
    # Perform search
    source_str = await async_search(query_list, max_search_depth)
    pinecone = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pinecone.IndexAsyncio(host=os.getenv("PINECONE_HOST", ""))
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    pinecone_search_str = await search_pinecone(
        index,
        embeddings,
        query_list,
        top_k,
        score_threshold,
    )

    source_str = pinecone_search_str + "\n\n" + source_str

    return {
        "source_str": source_str,
        "search_iterations": state["search_iterations"] + 1,
    }


async def write_and_grade_sections(
    state: SectionState, config: RunnableConfig
) -> Command[Literal[END, "search_web_rag"]]:
    """Write the section content and grade the section for quality.
    Quality pass if the section has enough content, is relevant to the section topic and description.
    If fail, then trigger more search queries to gather more context.

    Args:
        state: Current state containing section details
        config: Configuration including the grading model

    Returns:
        Command to mark section as completed or trigger more search queries
    """
    # Get state
    topic = state["topic"]
    section = state["section"]
    source_str = state["source_str"]

    # Get configuration
    my_config = Configuration.from_runnable_config(config)

    # Write the section content
    writer_provider = my_config.writer_provider
    writer_model_name = my_config.writer_model
    writer_model = init_chat_model(
        model_provider=writer_provider, model=writer_model_name
    )
    section_writer_inputs_formatted = section_writer_inputs.format(
        topic=topic,
        section_name=section.name,
        section_topic=section.description,
        context=source_str,
        section_content=section.content,
    )
    messages = [
        SystemMessage(content=section_writer_instructions),
        HumanMessage(content=section_writer_inputs_formatted),
    ]
    section_content = await writer_model.ainvoke(messages)
    section.content = section_content.content

    grading_provider = my_config.planner_provider
    grading_model_name = my_config.planner_model
    grading_model = init_chat_model(
        model_provider=grading_provider, model=grading_model_name
    )
    grading_model_with_structured_output = grading_model.with_structured_output(
        Feedback
    )
    section_grader_instructions_formatted = section_grader_instructions.format(
        topic=topic,
        section_topic=section.description,
        section=section.content,
        number_of_follow_up_queries=my_config.number_of_queries,
    )
    section_grader_message = (
        "Grade the report and consider follow-up questions for missing information. "
        "If the grade is 'pass', return empty strings for all follow-up queries. "
        "If the grade is 'fail', provide specific search queries to gather missing information."
    )

    messages = [
        SystemMessage(content=section_grader_instructions_formatted),
        HumanMessage(content=section_grader_message),
    ]
    feedback = await grading_model_with_structured_output.ainvoke(messages)

    # Check if the section is complete
    if (
        feedback.grade == "pass"
        or state["search_iterations"] >= my_config.max_search_depth
    ):
        # Publish the section to completed sections
        return Command(update={"completed_sections": [section]}, goto=END)

    # Update the existing section with new content and update search queries
    else:
        return Command(
            update={"search_queries": feedback.follow_up_queries, "section": section},
            goto="search_web",
        )


async def write_roadmap_conclusion(state: SectionState, config: RunnableConfig):
    """Write the introduction and conclusion of the report.

    Args:
        state: Current state with completed sections as context
        config: Configuration for writing model

    Returns:
        Dict containing the introduction and conclusion
    """
    # Get state
    topic = state["topic"]
    section = state["section"]
    completed_report_sections = state["report_sections_from_research"]

    my_config = Configuration.from_runnable_config(config)

    # Format system instructions
    section_specific_task_instructions = ""
    section_specific_quality_checks = ""

    if "Introduction" in section.name:
        section_specific_task_instructions = introduction_section_task
        section_specific_quality_checks = introduction_section_quality_checks
    elif "Roadmap" in section.name:
        section_specific_task_instructions = roadmap_section_task
        section_specific_quality_checks = roadmap_section_quality_checks
    elif "Conclusion/Summary" in section.name:
        section_specific_task_instructions = conclusion_section_task
        section_specific_quality_checks = conclusion_section_quality_checks

    system_instructions = final_section_writer_instructions.format(
        topic=topic,
        section_name=section.name,
        section_topic=section.description,
        context=completed_report_sections,
        task=section_specific_task_instructions,
        quality_checks=section_specific_quality_checks,
    )

    # Generate section
    writer_provider = my_config.writer_provider
    writer_model_name = my_config.writer_model
    writer_model = init_chat_model(
        model=writer_model_name, model_provider=writer_provider
    )

    section_content = await writer_model.ainvoke(
        [
            SystemMessage(content=system_instructions),
            HumanMessage(
                content="Generate a report section based on the provided sources."
            ),
        ]
    )

    # Write content to section
    section.content = section_content.content

    # Write the updated section to completed sections
    return {"completed_sections": [section]}


def collect_completed_sections(state: ReportState, config: RunnableConfig):
    """Collect the completed sections and generate the final report.

    Args:
        state: Current state with completed sections as context
        config: Configuration for writing model
    Returns:
        Dict with formatted sections as context
    """
    completed_sections = state["completed_sections"]

    # Format completed section to str to use as context for final sections
    completed_report_sections = format_sections(completed_sections)

    return {"report_sections_from_research": completed_report_sections}


def compile_final_report(state: ReportState):
    """Compile all sections into the final report.

    This node:
    1. Gets all completed sections
    2. Orders them according to original plan
    3. Combines them into the final report

    Args:
        state: Current state with all completed sections

    Returns:
        Dict containing the complete report
    """

    # Get sections
    sections = state["sections"]
    completed_sections = {s.name: s.content for s in state["completed_sections"]}

    # Update sections with completed content while maintaining original order
    for section in sections:
        if section.name in completed_sections:
            section.content = completed_sections[section.name]

    # Compile final report
    all_sections = "\n\n".join([s.content for s in sections])

    return {"final_report": all_sections}


def initiate_final_section_writing(state: ReportState):
    """Create parallel tasks for writing non-research sections.

    This edge function identifies sections that don't need research and
    creates parallel writing tasks for each one.

    Args:
        state: Current state with all sections and research context

    Returns:
        List of Send commands for parallel section writing
    """

    # Kick off section writing in parallel via Send() API for any sections that do not require research
    return [
        Send(
            "write_roadmap_conclusion",
            {
                "topic": state["topic"],
                "section": s,
                "report_sections_from_research": state["report_sections_from_research"],
            },
        )
        for s in state["sections"]
        if not s.research
    ]


section_workflow = StateGraph(SectionState, output=SectionOutputState)

section_workflow.add_node("section_generate_query", section_generate_query)
section_workflow.add_node("search_web_rag", search_web)
# section_workflow.add_node("search_rag", search_rag)
section_workflow.add_node("write_and_grade_section", write_and_grade_sections)

section_workflow.add_edge(START, "section_generate_query")
section_workflow.add_edge("section_generate_query", "search_web_rag")
# section_workflow.add_edge("section_generate_query_node", "search_rag")
section_workflow.add_edge("search_web_rag", "write_and_grade_section")
# section_workflow.add_edge("search_rag", "write_section")
# Define a new graph
report_workflow = StateGraph(
    ReportState,
    input=ReportStateInput,
    output=ReportStateOutput,
    config_schema=Configuration,
)

report_workflow.add_node("is_valid_job_description", is_valid_job_description)
report_workflow.add_node("planning_node", planning_node)
report_workflow.add_node("map_section_generation", map_section_generation)
report_workflow.add_node("generate_sections", section_workflow.compile())
report_workflow.add_node("collect_sections", collect_completed_sections)
report_workflow.add_node("write_roadmap_conclusion", write_roadmap_conclusion)
report_workflow.add_node("compile_final_report", compile_final_report)

report_workflow.add_edge(START, "is_valid_job_description")
report_workflow.add_edge("planning_node", "map_section_generation")
report_workflow.add_edge("generate_sections", "collect_sections")
report_workflow.add_conditional_edges(
    "collect_sections", initiate_final_section_writing, ["write_roadmap_conclusion"]
)
report_workflow.add_edge("write_roadmap_conclusion", "compile_final_report")
report_workflow.add_edge("compile_final_report", END)


graph = report_workflow.compile()


async def main():
    sample_jd = """Full job description
Minimum qualifications:
Bachelor's degree or equivalent practical experience.
2 years of experience with software development in one or more programming languages, or 1 year of experience with an advanced degree.
2 years of experience with data structures or algorithms in an academic or industry setting.
2 years of experience with backend or fullstack software development.
Preferred qualifications:
Master's degree or PhD in Computer Science or a related technical field.
2 years of experience with performance, systems data analysis, visualization tools, or debugging.
Experience in developing accessible technologies.
Experience in code and system health, diagnosis and resolution, and software test engineering.
Experience with C++ and SQL.
About the job

Google's software engineers develop the next-generation technologies that change how billions of users connect, explore, and interact with information and one another. Our products need to handle information at massive scale, and extend well beyond web search. We're looking for engineers who bring fresh ideas from all areas, including information retrieval, distributed computing, large-scale system design, networking and data storage, security, artificial intelligence, natural language processing, UI design and mobile; the list goes on and is growing every day. As a software engineer, you will work on a specific project critical to Google’s needs with opportunities to switch teams and projects as you and our fast-paced business grow and evolve. We need our engineers to be versatile, display leadership qualities and be enthusiastic to take on new problems across the full-stack as we continue to push technology forward.Google Ads operates across several countries and is composed of the engineering teams like Search Ads, Display, Video Ads and Apps (AViD), YouTube Ads, Analytics, Insights and Measurements (AIM), Ads Privacy and Safety (APaS), Commerce, Travel and Customer Engagement, and two Departments: Reach User Experience (UX) and Ads Engineering Productivity.Google Ads is helping power the open internet with the best technology that connects and creates value for people, publishers, advertisers, and Google. We’re made up of multiple teams, building Google’s Advertising products including search, display, shopping, travel and video advertising, as well as analytics. Our teams create trusted experiences between people and businesses with useful ads. We help grow businesses of all sizes from small businesses, to large brands, to YouTube creators, with effective advertiser tools that deliver measurable results. We also enable Google to engage with customers at scale.The US base salary range for this full-time position is $141,000-$202,000 + bonus + equity + benefits. Our salary ranges are determined by role, level, and location. Within the range, individual pay is determined by work location and additional factors, including job-related skills, experience, and relevant education or training. Your recruiter can share more about the specific salary range for your preferred location during the hiring process.Please note that the compensation details listed in US role postings reflect the base salary only, and do not include bonus, equity, or benefits. Learn more aboutbenefits at Google.
Responsibilities

Design, develop, test, deploy, maintain, and improve software.
Manage person's project priorities, deadlines, and deliverables."""

    output = await graph.ainvoke({"topic": sample_jd})
    return output


if __name__ == "__main__":
    load_dotenv()

    # with open("./graph.md", "w") as f:
    #     f.write(graph.get_graph(xray=1).draw_mermaid())
    final = asyncio.run(main())
    with open("report.md", "w") as f:
        f.write(final["final_report"])
