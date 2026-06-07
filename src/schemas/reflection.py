from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Optional


OperationType = Literal[
    "HOOK_STRENGTHENING",
    "CLARITY_IMPROVEMENT",
    "TRANSITION_IMPROVEMENT",
    "VALUE_CLARIFICATION",
    "CONCISENESS",
    "REORDERING",
    "REDUNDANCY_REMOVAL",
    "CTA_IMPROVEMENT",
    "EXPLICITATION"
]


class Operation(BaseModel):
    op: OperationType = Field(
        ...,
        description="Type of edit operation."
    )

    target: str = Field(
        ...,
        description="Target paragraph/sentence."
    )

    instruction: Optional[str] = Field(
        default=None,
        description="How to apply the operation."
    )

    to_position: Optional[int] = Field(
        default=None,
        description="Used for reordering."
    )


class ReflectionResult(BaseModel):
    priority_issues: List[str] = Field(
        default_factory=list
    )

    strengths_to_preserve: List[str] = Field(
        default_factory=list
    )

    operations: List[Operation] = Field(
        default_factory=list
    )

    constraints: Dict[str, bool] = Field(
        default_factory=lambda: {
            "no_new_information": True,
            "no_story_addition": True,
            "preserve_meaning": True
        }
    )

    done: bool = Field(
        default=False,
        description="True if no more meaningful edits are needed."
    )