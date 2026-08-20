from pydantic import BaseModel, Field
from typing import List, Literal

class Scores(BaseModel):
    hook: int = Field(..., ge=1, le=10, description="Ability of opening to capture attention.")
    clarity: int = Field(..., ge=1, le=10, description="How clear and understandable the post is.")
    engagement: int = Field(..., ge=1, le=10, description="Likelihood of generating comments or reactions.")
    authenticity: int = Field(..., ge=1, le=10, description="How human and non-generic the post feels.")
    professionalism: int = Field(..., ge=1, le=10, description="Appropriateness for LinkedIn tone.")
    structure: int = Field(..., ge=1, le=10, description="Logical flow and readability.")
    faithfulness: int = Field(..., ge=1, le=10, description="Strict adherence to original input without hallucination.")

class ImprovementOpportunity(BaseModel):
    category: str = Field(..., description="E.g., Hook, Engagement, Conciseness, Structure")
    priority: Literal["Low", "Medium", "High", "Critical"] = Field(..., description="Priority level of the improvement")
    reason: str = Field(..., description="Explanation of what to improve and why it matters")
    recommendation: str = Field(..., description="High-level recommendation without rewriting the text")

class EvaluationResult(BaseModel):
    scores: Scores = Field(..., description="Multi-dimensional scoring of the LinkedIn post.")
    
    strengths: List[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 things that are already working well in the post."
    )

    weaknesses: List[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 key issues reducing quality or impact."
    )

    improvement_opportunities: List[ImprovementOpportunity] = Field(
        ...,
        min_length=2,
        description="At least 2 actionable improvements detailing what to fix, why, and how."
    )

    feedback: str = Field(
        ...,
        description="Concise 2-4 sentence overall assessment and actionable feedback."
    )

    needs_improvement: bool = Field(
        default=False,
        description="True if post requires refinement (e.g., if any score is below an 8)."
    )