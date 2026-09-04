from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class OptimizeRequest(BaseModel):
    thread_id: str
    topic: str
    brief: Dict[str, Any]
    tone: Optional[str] = "Direct, punchy, and technical (like a senior engineer)"
    needs_live_context: Optional[bool] = False

class FeedbackRequest(BaseModel):
    thread_id: str
    feedback: Optional[str] = None
    approved_references: Optional[List[Dict[str, Any]]] = None

class OptimizeResponse(BaseModel):
    thread_id: str
    post: str
    verdict: Dict[str, Any]
    evaluation: Dict[str, Any]
    iteration: int
    status: str
    proposed_references: Optional[List[Dict[str, Any]]] = None
    reasoning_steps: List[str] = []