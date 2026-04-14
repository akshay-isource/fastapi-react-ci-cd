"""
FASTAPI ENTRY POINT

Exposes the multi-agent research workflow as an API.
The React frontend connects to this server.

Endpoints:
    GET  /health          — Health check
    POST /research        — Run the full pipeline, return the report
    POST /research/stream — Stream agent progress in real-time (SSE)
"""

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from graph.workflow import research_workflow

app = FastAPI(title="AI Research Team", version="1.0.0")

# Allow the React frontend (localhost:3000) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    query: str


class ResearchResponse(BaseModel):
    query: str
    research_data: str
    analysis: str
    final_report: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AI Research Team"}


@app.post("/research", response_model=ResearchResponse)
async def run_research(request: ResearchRequest):
    """
    Run the full multi-agent research pipeline.

    Flow: User Query → Researcher → Analyst → Writer → Report
    """

    # Initialize the state with the user's query
    # Empty strings/lists for fields that agents will fill
    # research_pieces starts as [] — parallel researchers will append to it
    initial_state = {
        "query": request.query,
        "research_pieces": [],
        "research_data": "",
        "analysis": "",
        "final_report": "",
        "messages": [],
        "retry_count": 0,
        "quality_score": 0,
        "feedback": "",
        "targeted_feedback": {},
    }

    # Run the graph — 3 researchers run in parallel, then merge → analyze → check → write
    # On retry, the loop goes: dispatcher → 3 researchers → merger → analyst → checker
    result = await research_workflow.ainvoke(initial_state)

    return ResearchResponse(
        query=result["query"],
        research_data=result["research_data"],
        analysis=result["analysis"],
        final_report=result["final_report"]
    )


@app.post("/research/stream")
async def stream_research(request: ResearchRequest):
    """
    Stream the research pipeline progress using Server-Sent Events.
    The frontend can show which agent is currently working.
    """

    import json

    async def event_generator():
        initial_state = {
            "query": request.query,
            "research_pieces": [],
            "research_data": "",
            "analysis": "",
            "final_report": "",
            "messages": [],
            "retry_count": 0,
            "quality_score": 0,
            "feedback": "",
            "targeted_feedback": {},
        }

        # astream_events gives us real-time updates as each node runs
        async for event in research_workflow.astream(
            initial_state,
            stream_mode="updates"
        ):
            # event is a dict like {"researcher": {"research_data": "..."}}
            for node_name, node_output in event.items():
                # Some nodes (like dispatcher) return {} or None — skip gracefully
                if not node_output:
                    data = {"agent": node_name, "status": "completed", "data": {}}
                    yield f"data: {json.dumps(data)}\n\n"
                    continue
                # Send full data for report-critical fields,
                # truncate large fields that are only for side panels
                filtered = {}
                for k, v in node_output.items():
                    if k == "messages":
                        continue  # skip message history
                    if k == "research_pieces":
                        continue  # skip raw pieces (merger combines them)
                    filtered[k] = v
                data = {
                    "agent": node_name,
                    "status": "completed",
                    "data": filtered
                }
                yield f"data: {json.dumps(data)}\n\n"

        yield f"data: {json.dumps({'agent': 'pipeline', 'status': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
