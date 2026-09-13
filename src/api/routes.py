from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.api.schema import OptimizeRequest, FeedbackRequest, OptimizeResponse
from src.api.service import (
    stream_pipeline_events,
    resume_pipeline,
    get_pipeline_state
)
from src.agents.workflow import app, research_agent

router = APIRouter(prefix="/api", tags=["pipeline"])

@router.post("/optimize/stream")
async def optimize_stream(request: OptimizeRequest):
    """Streams live step-by-step progress via Server-Sent Events (SSE)."""
    try:
        return StreamingResponse(
            stream_pipeline_events(
                thread_id=request.thread_id,
                topic=request.topic,
                brief=request.brief,
                tone=request.tone,
                needs_live_context=request.needs_live_context
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume", response_model=OptimizeResponse)
async def resume_post(request: FeedbackRequest):
    """Resumes after HITL checkpoints (feedback or research review)."""
    try:
        return await resume_pipeline(
            thread_id=request.thread_id,
            feedback=request.feedback,
            approved_references=request.approved_references
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/{thread_id}", response_model=OptimizeResponse)
def get_state(thread_id: str):
    """Fetches the latest state and reasoning steps."""
    try:
        return get_pipeline_state(thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from src.agents.curator import get_curated_topics
from src.schemas.curator import CuratedOptions
from src.schemas.perspective import QuestionSet
from src.services.perspective_service import start_interview, probe_interview, finish_interview
from src.store.run_store import save_brief
from src.services.search_service import fetch_live_context
from src.api.schema import (
    StartInterviewRequest, 
    ProbeInterviewRequest, 
    FinishInterviewRequest, 
    FinishInterviewResponse, 
    LiveContextRequest
)
from typing import List, Dict, Any

USER_ID = "demo-user"

@router.get("/curate", response_model=CuratedOptions)
def curate_topics(category: str):
    """Fetches trending news and curates it into structured options."""
    try:
        return get_curated_topics(category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interview/start", response_model=QuestionSet)
def api_start_interview(request: StartInterviewRequest):
    """Generates initial questions based on topic and tone."""
    try:
        return start_interview(USER_ID, request.topic, request.tone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interview/probe", response_model=QuestionSet)
def api_probe_interview(request: ProbeInterviewRequest):
    """Checks answers and generates follow-up questions for thin answers."""
    try:
        return probe_interview(USER_ID, request.topic, request.answers, request.tone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interview/finish", response_model=FinishInterviewResponse)
def api_finish_interview(request: FinishInterviewRequest):
    """Synthesizes the brief and saves it to the run store."""
    try:
        brief = finish_interview(USER_ID, request.topic, request.answers, request.tone)
        brief_id = save_brief(USER_ID, brief, request.answers, request.was_probed)
        return FinishInterviewResponse(brief_id=str(brief_id), brief=brief)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/research/live", response_model=List[Dict[str, str]])
def api_live_context(request: LiveContextRequest):
    """Searches the web for current data supporting the thesis."""
    try:
        return fetch_live_context(topic=request.topic, thesis=request.thesis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))