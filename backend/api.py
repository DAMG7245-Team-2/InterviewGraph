import uuid
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from langgraph.types import Command

from interview_agent.graph import graph_with_checkpoint as interview_agent_graph
from prep_agent.graph import graph as prep_agent_graph
from pydantic import BaseModel, Field

app = FastAPI()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class UserInput(BaseModel):
    message: str = Field(description="Message from the user")
    thread_id: str | None = Field(
        description="Thread ID to persist and continue a multi-turn conversation.",
        default=None,
    )


class PrepInput(BaseModel):
    job_description: str = Field(description="Job description", min_length=50)


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


@app.post("/interview")
async def invoke_interview(user_input: UserInput):
    try:
        kwargs = await _handle_user_input(user_input)
        response_with_events = await interview_agent_graph.ainvoke(
            **kwargs, stream_mode=["updates", "values"]
        )
        logger.debug(f"response_with_events: {response_with_events}")

        response_type, response = response_with_events[-1]
        logger.info(
            f"last response: response_type={response_type}, response={response}"
        )

        if response_type == "values":
            if "feedback" in response:
                output = response["feedback"]
            else:
                output = "No response from agent"
        elif response_type == "updates" and "__interrupt__" in response:
            output = response["__interrupt__"][0].value
        else:
            raise ValueError(f"Unexpected response type: {response_type}")

        return output
    except Exception as e:
        logger.error(f"Error in invoke_interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prep")
async def invoke_prep(prep_input: PrepInput):
    try:
        output = await prep_agent_graph.ainvoke({"topic": prep_input.job_description})
        logger.info(f"prep output: first 100 chars: {output['final_report'][:100]}")

        with open("final_report.md", "w") as f:
            f.write(output["final_report"])

        return FileResponse("final_report.md", media_type="text/markdown")

    except Exception as e:
        logger.error(f"Error in invoke_prep: {e}")
        raise HTTPException(status_code=500, detail=str(e))
