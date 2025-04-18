import os
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langchain.chat_models import init_chat_model
from sqlalchemy import create_engine
from dotenv import load_dotenv
from snowflake.sqlalchemy import URL

from interview_agent.state import State, InputState, QAList, Feedback
from interview_agent.util import (
    aget_randomized_interview_questions,
    AvailableCategories,
    AvailableDifficulties,
)
from interview_agent.prompts import (
    START_INTERVIEW,
    WAIT_FOR_USER_INTERRUPT_MESSAGE,
    quizzer_prompt,
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
    """Generate a question based on the context provided."""
    # Initialize the chat model
    myconfig = Configuration.from_runnable_config(config)
    num_questions = myconfig.number_of_questions
    quizzer_provider = myconfig.quizzer_provider
    quizzer_model = myconfig.quizzer_model

    chat_model = init_chat_model(model_provider=quizzer_provider, model=quizzer_model)
    chat_model_with_structured_output = chat_model.with_structured_output(QAList)
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
    context = await aget_randomized_interview_questions(
        engine,
        AvailableCategories.ALGORITHMS,
        AvailableDifficulties.HARD,
        num_questions,
    )

    system_message = SystemMessage(
        content=quizzer_prompt.format(
            num_questions=num_questions,
            context=context,
        )
    )
    human_message = HumanMessage(
        content="Please generate a question based on the provided context."
    )

    # Send the messages to the chat model and get the response
    response = await chat_model_with_structured_output.ainvoke(
        [system_message, human_message]
    )
    generated_qa_list = response.qa_list
    return {"qa_list": generated_qa_list}


async def wait_for_user_input(
    state: State, config: RunnableConfig
) -> Command[Literal["human_node", "wait_for_user_input_node"]]:
    """Wait for the user to start the interview."""
    user_input = interrupt(WAIT_FOR_USER_INTERRUPT_MESSAGE)
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
