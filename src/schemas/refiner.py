from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Optional


HookType = Literal[
    "question",
    "statement",
    "story",
    "insight",
    "vulnerability"
]

EngagementLevel = Literal["low", "medium", "high"]


class ChangeApplied(BaseModel):
    op: str = Field(
        ...,
        description="Operation applied (e.g., REPHRASE, REORDER, CTA_IMPROVEMENT)."
    )

    target: str = Field(
        ...,
        description="Part of the post that was modified."
    )

    description: str = Field(
        ...,
        description="Short explanation of the change applied."
    )


class FaithfulnessCheck(BaseModel):
    passed: bool = Field(
        ...,
        description="Whether final output stayed faithful to original content."
    )

    notes: Optional[str] = Field(
        None,
        description="Any detected issues with hallucination or drift."
    )


class RefinerResult(BaseModel):
    final_post: str = Field(
        ...,
        description="Final improved LinkedIn post."
    )

    changes_applied: List[ChangeApplied] = Field(
        ...,
        description="Traceable list of edits performed."
    )

    hook_type: HookType = Field(
        ...,
        description="Type of hook used in final version."
    )

    expected_engagement_level: EngagementLevel = Field(
        ...,
        description="Estimated engagement potential of the post."
    )

    faithfulness_check: FaithfulnessCheck = Field(
        ...,
        description="Validation that no new information was introduced."
    )