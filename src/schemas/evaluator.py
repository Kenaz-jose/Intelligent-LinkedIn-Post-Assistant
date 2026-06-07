from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class FaithfulnessAnalysis(BaseModel):
    is_faithful: bool = Field(
        ...,
        description="Whether the output strictly preserves meaning from input without adding new facts, events, or experiences."
    )
    violations: List[str] = Field(
        default_factory=list,
        description="List of detected hallucinations or unsupported additions."
    )
    notes: Optional[str] = Field(
        None,
        description="Additional explanation about faithfulness issues."
    )


class Scores(BaseModel):
    hook: int = Field(..., ge=0, le=10, description="Ability of opening to capture attention.")
    clarity: int = Field(..., ge=0, le=10, description="How clear and understandable the post is.")
    engagement: int = Field(..., ge=0, le=10, description="Likelihood of generating comments or reactions.")
    authenticity: int = Field(..., ge=0, le=10, description="How human and non-generic the post feels.")
    professionalism: int = Field(..., ge=0, le=10, description="Appropriateness for LinkedIn tone.")
    structure: int = Field(..., ge=0, le=10, description="Logical flow and readability.")
    faithfulness: int = Field(..., ge=0, le=10, description="Strict adherence to original input without hallucination.")


class EvaluationResult(BaseModel):
    scores: Scores = Field(..., description="Multi-dimensional scoring of the LinkedIn post.")
    
    improvement_priority: List[str] = Field(
        ...,
        description="Top 3 areas to improve ranked by impact (e.g., Hook, Engagement, Structure)."
    )

    strengths: List[str] = Field(
        ...,
        description="What is already working well in the post."
    )

    weaknesses: List[str] = Field(
        ...,
        description="Key issues reducing quality or impact."
    )

    faithfulness_analysis: FaithfulnessAnalysis = Field(
        ...,
        description="Assessment of whether the content introduces any unsupported information."
    )

    feedback: str = Field(
        ...,
        description="Concise actionable feedback for improvement (no rewriting)."
    )

    needs_improvement: bool = Field(
        default=False,
        description="True if post requires refinement"
    )