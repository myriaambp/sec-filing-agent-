import os
import json
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent_definitions.orchestrator import run_analysis

app = FastAPI(title="FilingLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    question: str


@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    """Stream agent progress events and final result as newline-delimited JSON."""

    async def stream():
        async for event in run_analysis(request.question):
            yield json.dumps(event) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@app.get("/health")
def health():
    return {"status": "ok"}
