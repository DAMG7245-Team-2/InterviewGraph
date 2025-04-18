from typing import Literal
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from interview_agent.state import (
    QA,
    SQLTOOL_ARGS_SCHEMA,
    QList,
    State,
    InputState,
    Feedback,
)
from interview_agent.prompts import (
    START_INTERVIEW,
    WAIT_FOR_USER_INTERRUPT_MESSAGE,
    feedback_prompt,
)
from interview_agent.configuration import Configuration
from prep_agent.state import JobDescriptionValidation

load_dotenv()


async def collect_job_description(state: State, config: RunnableConfig):
    interrupt_message = "Please provide a valid job description"
    job_description = interrupt(interrupt_message)
    return {"job_description": job_description}


async def is_valid_job_description(
    state: State, config: RunnableConfig
) -> Command[Literal["generate_question_node", "collect_jd_node"]]:
    my_config = Configuration.from_runnable_config(config)
    job_description = state["job_description"]
    quizzer_provider = my_config.quizzer_provider
    quizzer_model = my_config.quizzer_model
    validator_model = init_chat_model(
        model_provider=quizzer_provider, model=quizzer_model
    )
    structured_llm = validator_model.with_structured_output(JobDescriptionValidation)
    system_instructions = "You are a job description validator. You will be given a text and you will need to validate if it is a valid job description. If the job description is not valid, you will return 'invalid'. If the job description is valid, you will return 'valid'."
    messages = [
        SystemMessage(content=system_instructions),
        HumanMessage(content=job_description),
    ]
    results = await structured_llm.ainvoke(messages)
    print("Job description validation results: ", results)
    if results.valid == "valid":
        return Command(goto="generate_question_node")
    else:
        return Command(goto="collect_jd_node")


async def generate_question(state: State, config: RunnableConfig):
    """Analyze the job description and return a list of questions."""
    # Get the project root directory (4 levels up from this file)
    project_root = Path(__file__).parent.parent.parent.parent
    sql_mcp_path = project_root / "sql_mcp.py"

    server_params = StdioServerParameters(
        command="python",
        args=[str(sql_mcp_path)],
    )
    model = ChatOpenAI(model="gpt-4o-mini")
    my_config = Configuration.from_runnable_config(config)
    num_questions = my_config.number_of_questions


    def generate_question_message(job_description: str, num_questions: int):
        return f"You are an interviewer. You will be crafting questions for a phone interview using the tool 'sql_tool'. The tool is a database of interview questions and answers. Generate a list of {num_questions} possible interview questions based on the job description provided. \n Job Description: {job_description}"

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Get tools
            tools = await load_mcp_tools(session)

            tools[0].args_schema = SQLTOOL_ARGS_SCHEMA

            # Create and run the agent
            agent = create_react_agent(model, tools, response_format=QList)
            agent_response = await agent.ainvoke(
                {
                    "messages": generate_question_message(
                        state["job_description"], num_questions
                    )
                }
            )
            state["qa_list"] = []
            for qa in agent_response["structured_response"].q_list:
                state["qa_list"].append(
                    QA(
                        question=qa.question,
                        expected_answer=qa.answer,
                        given_answer="",
                    )
                )
            return {"qa_list": state["qa_list"]}


async def wait_for_user_input(
    state: State, config: RunnableConfig
) -> Command[Literal["human_node", "wait_for_user_input_node"]]:
    """Wait for the user to start the interview."""
    user_input = interrupt(f"{len(state['qa_list'])}")
    if user_input == START_INTERVIEW:
        return Command(goto="human_node")
    else:
        return Command(goto="wait_for_user_input_node")


async def human_node(state: State, config: RunnableConfig):
    """Human node to get the answer from the user."""

    current_qa = state["qa_list"][len(state["completed_qa"])]
    user_answer = interrupt(current_qa.question)
    current_qa.given_answer = user_answer

    return {"completed_qa": [current_qa]}


async def generate_feedback(state: State, config: RunnableConfig):
    """Generate feedback based on the answer provided by the user."""
    # Initialize the chat model
    myconfig = Configuration.from_runnable_config(config)
    feedback_provider = myconfig.feedback_provider
    feedback_model = myconfig.feedback_model
    chat_model = init_chat_model(model_provider=feedback_provider, model=feedback_model)

    chat_model_with_structured_output = chat_model.with_structured_output(Feedback)

    responses = []
    for qa in state["completed_qa"]:
        system_message = SystemMessage(content=feedback_prompt.format(qa=qa))
        human_message = HumanMessage(
            content="Please generate feedback based on the provided context."
        )

        response = await chat_model_with_structured_output.ainvoke(
            [system_message, human_message]
        )
        responses.append(response)

    return {"feedback": responses}


def route(state: State) -> Literal["human_node", "feedback_node"]:
    if len(state["qa_list"]) == len(state["completed_qa"]):
        return "feedback_node"
    else:
        return "human_node"


poc_workflow = StateGraph(State, input=InputState, config_schema=Configuration)
poc_workflow.add_node("collect_jd_node", collect_job_description)
poc_workflow.add_node("validate_job_description_node", is_valid_job_description)
poc_workflow.add_node("generate_question_node", generate_question)
poc_workflow.add_node("wait_for_user_input_node", wait_for_user_input)
poc_workflow.add_node("human_node", human_node)
poc_workflow.add_node("feedback_node", generate_feedback)

poc_workflow.add_edge(START, "validate_job_description_node")
poc_workflow.add_edge("collect_jd_node", "validate_job_description_node")
poc_workflow.add_edge("generate_question_node", "wait_for_user_input_node")
poc_workflow.add_conditional_edges("human_node", route)
poc_workflow.add_edge("feedback_node", END)

graph = poc_workflow.compile()

graph_with_checkpoint = poc_workflow.compile(checkpointer=MemorySaver())
