import logging
import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
from interview_agent.graph import graph_with_checkpoint as interview_agent_graph
from langgraph.types import Command
from prep_agent.graph import graph as prep_agent_graph
from pydantic import BaseModel, Field

load_dotenv()

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


class TTSInput(BaseModel):
    text: str
    voice_id: str

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
        return {"final_report": output["final_report"]}
    except Exception as e:
        logger.error(f"Error in invoke_prep: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts")
async def text_to_speech(input: TTSInput):
    ELEVEN_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
    if not ELEVEN_API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{input.voice_id}",
                headers={
                    "Content-Type": "application/json",
                    "xi-api-key": ELEVEN_API_KEY,
                },
                json={
                    "text": input.text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    },
                },
                timeout=30.0
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return StreamingResponse(response.aiter_bytes(), media_type="audio/mpeg")

    except Exception as e:
        logger.error(f"ElevenLabs error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate speech")