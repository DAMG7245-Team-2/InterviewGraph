import uuid

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from interview_agent.graph import graph_with_checkpoint as interview_agent_graph
from langgraph.types import Command
from prep_agent.graph import graph as prep_agent_graph
from pydantic import BaseModel, Field

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

class UserInput(BaseModel):
    message: str
    thread_id: str = Field(
        description="Thread ID to persist and continue a multi-turn conversation.",
        default=None,
    )

class PrepRequest(BaseModel):
    job_description: str


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {"status": "ok"}


async def _handle_user_input(user_input: UserInput):
    thread_id = user_input.thread_id or str(uuid.uuid4())
    print(f"Creating new thread with ID: {thread_id}")
    config = {"configurable": {"thread_id": thread_id}}
    state = await interview_agent_graph.aget_state(config=config)
    interrupted_tasks = [
        task for task in state.tasks if hasattr(task, "interrupts") and task.interrupts
    ]
    if interrupted_tasks:
        input = Command(resume=user_input.message)
    else:
        input = {"topic": user_input.message}
    kwargs = {
        "input": input,
        "config": config,
    }
    return kwargs


@app.post("/interview/")
async def invoke_interview(user_input: UserInput):
    try:
        kwargs = await _handle_user_input(user_input)
        response_with_events = await interview_agent_graph.ainvoke(
            **kwargs, stream_mode=["updates", "values"]
        )
        response_type, response = response_with_events[-1]
        if response_type == "values":
            print(response)
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/prep")
async def invoke_prep(request: PrepRequest):
    try:
        output = await prep_agent_graph.ainvoke({"topic": request.job_description})
        return {"final_report": output["final_report"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
