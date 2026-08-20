from pydantic import BaseModel, Field
from typing import List, Literal

class EditOperation(BaseModel):
    op: Literal[
        "HOOK_STRENGTHENING",
        "CTA_IMPROVEMENT",
        "TRANSITION_IMPROVEMENT",
        "CLARITY_IMPROVEMENT",
        "CONCISENESS",
        "REDUNDANCY_REMOVAL",
        "REORDERING",
        "EXPLICITATION",
        "FAITHFULNESS_CORRECTION"
    ] = Field(
        ..., 
        description="The specific type of edit operation to perform."
    )
    target_snippet: str = Field(
        ..., 
        description="A exact 3-5 word quote from the current draft identifying exactly where the edit should happen."
    )
    instruction: str = Field(
        ..., 
        description="Concise direction on what to change, referencing existing content only. Do not provide rewritten text."
    )

class ReflectionResult(BaseModel):
    priority_issues: List[str] = Field(
        ..., 
        description="List of the highest priority issues being addressed in this iteration (e.g., ['Hook', 'Faithfulness'])."
    )
    strengths_to_preserve: List[str] = Field(
        ..., 
        description="List of elements that are working well and should not be modified."
    )
    operations: List[EditOperation] = Field(
        ..., 
        description="List of specific edit operations to apply. Should be empty if done is true."
    )
    done: bool = Field(
        ..., 
        description="Set to true if no further high-impact edits are needed, or if the post is already stable and faithful."
    )