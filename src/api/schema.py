from pydantic import BaseModel
from typing import List, Dict, Any


class OptimizeRequest(BaseModel):
    topic: str


class OptimizeResponse(BaseModel):
    post: str
    evaluation: Dict[str, Any]
    reflection: Dict[str, Any]
    iteration: int
    scores: List[Dict[str, Any]]