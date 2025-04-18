from typing import List
import uuid
import logging

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from interview_agent.graph import graph_with_checkpoint as interview_agent_graph
from interview_agent.state import Feedback
from langgraph.types import Command
from prep_agent.graph import graph as prep_agent_graph
from pydantic import BaseModel, Field

app = FastAPI()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserInput(BaseModel):
    message: str = Field(description="Message from the user")
    thread_id: str | None = Field(
        description="Thread ID to persist and continue a multi-turn conversation.",
        default=None,
    )


class PrepInput(BaseModel):
    job_description: str = Field(description="Job description", min_length=50)


class InterviewResponse(BaseModel):
    message: str = Field(description="Output from the interview")
    feedback: List[Feedback] | None = Field(description="Feedback from the interview")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {"status": "ok"}


async def _handle_user_input(user_input: UserInput):
    thread_id = user_input.thread_id or str(uuid.uuid4())
    logger.info(f"Using thread ID: {thread_id}")

    config = {"configurable": {"thread_id": thread_id}}
    state = await interview_agent_graph.aget_state(config=config)
    logger.debug(f"interview_agent_graph state: {state}")

    interrupted_tasks = [
        task for task in state.tasks if hasattr(task, "interrupts") and task.interrupts
    ]
    logger.debug(f"found {len(interrupted_tasks)} interrupted tasks")

    if interrupted_tasks:
        input = Command(resume=user_input.message)
    else:
        input = {"job_description": user_input.message}

    kwargs = {
        "input": input,
        "config": config,
    }

    logger.debug(f"handled user input: {kwargs}")
    return kwargs


@app.post("/interview", status_code=200, response_model=InterviewResponse)
async def invoke_interview(user_input: UserInput, response: Response):
    try:
        kwargs = await _handle_user_input(user_input)

        response_with_events = await interview_agent_graph.ainvoke(
            **kwargs, stream_mode=["updates", "values"]
        )

        logger.debug(f"response_with_events: {response_with_events}")

        response_type, response_dict = response_with_events[-1]
        logger.info(
            f"last response: response_type={response_type}, response={response_dict}"
        )

        feedback = None
        if response_type == "values":
            if "feedback" in response_dict:
                feedback = response_dict["feedback"]
                output = "Interview complete"
            else:
                output = "No response from agent"
        elif response_type == "updates" and "__interrupt__" in response_dict:
            output = response_dict["__interrupt__"][0].value
            if "Please provide a valid job description" in output:
                response.status_code = 418
        else:
            raise ValueError(f"Unexpected response type: {response_type}")

        return InterviewResponse(message=output, feedback=feedback)
    except Exception as e:
        logger.error(f"Error in invoke_interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prep")
async def invoke_prep(prep_input: PrepInput):
    try:
        output = await prep_agent_graph.ainvoke({"topic": prep_input.job_description})
        logger.info(f"prep output: first 100 chars: {output['final_report'][:100]}")
        return {"final_report": output["final_report"]}
    except Exception as e:
        logger.error(f"Error in invoke_prep: {e}")
        raise HTTPException(status_code=500, detail=str(e))
