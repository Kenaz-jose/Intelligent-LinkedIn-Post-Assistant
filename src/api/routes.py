from fastapi import APIRouter
from src.api.schema import OptimizeRequest, OptimizeResponse
from src.api.service import run_pipeline

router = APIRouter()


@router.post("/optimize", response_model=OptimizeResponse)
def optimize_post(request: OptimizeRequest):

    result = run_pipeline(request.topic)

    return result