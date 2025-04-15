from fastapi import FastAPI, WebSocket
from interview_agent.graph import graph as interview_agent_graph
from prep_agent.graph import graph as prep_agent_graph

app = FastAPI()


@app.websocket("/interview/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        async for event in interview_agent_graph.astream(
            {"messages": [data]}, config=config, stream_mode="messages"
        ):
            await websocket.send_text(event[0].content)


@app.post("/prep")
async def invoke_prep(job_description: str):
    output = await prep_agent_graph.ainvoke({"topic": job_description})
    return output["final_report"]
