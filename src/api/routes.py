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