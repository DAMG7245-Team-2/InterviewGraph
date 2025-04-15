from typing import Literal
from interview_agent.configuration import Configuration
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langchain.chat_models import init_chat_model
from interview_agent.state import State, InputState, QAList, Feedback
from interview_agent.util import get_context
from interview_agent.prompts import quizzer_prompt, feedback_prompt


def generate_question(state: State, config: RunnableConfig):
    """Generate a question based on the context provided."""
    # Initialize the chat model
    myconfig = Configuration.from_runnable_config(config)
    num_questions = myconfig.number_of_questions
    quizzer_provider = myconfig.quizzer_provider
    quizzer_model = myconfig.quizzer_model

    chat_model = init_chat_model(model_provider=quizzer_provider, model=quizzer_model)
    chat_model_with_structured_output = chat_model.with_structured_output(QAList)

    context = get_context()
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
    response = chat_model_with_structured_output.invoke([system_message, human_message])
    # print("generate question llm response", response)
    # Extract the generated question from the response
    generated_qa_list = response.qa_list
    # print("generated_qa_list", generated_qa_list)
    return {"qa_list": generated_qa_list}


async def human_node(state: State, config: RunnableConfig):
    """Human node to get the answer from the user."""

    current_qa = state["qa_list"][len(state["completed_qa"])]
    user_answer = interrupt(current_qa.question)
    current_qa.given_answer = user_answer

    return {"completed_qa": [current_qa]}


def generate_feedback(state: State, config: RunnableConfig):
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

        response = chat_model_with_structured_output.invoke(
            [system_message, human_message]
        )
        responses.append(response)

    return {"feedback": responses}


def route(state: State) -> Literal["human_node", "feedback_node"]:
    if len(state["qa_list"]) == len(state["completed_qa"]):
        return "feedback_node"
    else:
        return "human_node"


poc_workflow = StateGraph(State, input=InputState)
poc_workflow.add_node("generate_question", generate_question)
poc_workflow.add_node("human_node", human_node)
poc_workflow.add_node("feedback_node", generate_feedback)

poc_workflow.add_edge(START, "generate_question")
poc_workflow.add_edge("generate_question", "human_node")
poc_workflow.add_conditional_edges("human_node", route)
poc_workflow.add_edge("feedback_node", END)

graph = poc_workflow.compile()

graph_with_checkpoint = poc_workflow.compile(checkpointer=MemorySaver())
