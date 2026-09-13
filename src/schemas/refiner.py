from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class OperationStatus(BaseModel):
    op: str = Field(
        ...,
        description="The operation type that was attempted (e.g., HOOK_STRENGTHENING, CLARITY_IMPROVEMENT)."
    )
    
    target_snippet: str = Field(
        ...,
        description="The specific text snippet that was targeted for this operation."
    )
    
    status: Literal["applied", "skipped"] = Field(
        ...,
        description="Whether the edit was successfully applied or skipped due to missing information/conflict."
    )
    
    reason: str = Field(
        ...,
        description="Short explanation of how the change was applied, or why it was skipped."
    )

class FaithfulnessCheck(BaseModel):
    passed: bool = Field(
        ...,
        description="Whether the final output stayed strictly faithful to original content (no new facts)."
    )
    
    notes: Optional[str] = Field(
        None,
        description="Any detected issues with hallucination, or confirmation of faithfulness."
    )

class RefinerResult(BaseModel):
    final_post: str = Field(
        ...,
        description="The final, polished LinkedIn post."
    )
    
    changes_applied: List[OperationStatus] = Field(
        ...,
        description="Traceable list of operations that were successfully executed."
    )
    
    skipped_operations: List[OperationStatus] = Field(
        default_factory=list,
        description="List of operations that were skipped because they conflicted or required inventing new information."
    )
    
    faithfulness_check: FaithfulnessCheck = Field(
        ...,
        description="Validation that no new information was introduced into the post."
    )