from pydantic import BaseModel, Field
from typing import List, Literal

from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    """
    Assessment before number.

    The model must first state what it observed in the text
    before committing to a score. This makes the score a
    conclusion based on evidence rather than a first impression.
    """
    observation: str = Field(
        ...,
        description=(
            "One sentence quoting or describing the specific text that determines this score."
        ),
    )
    score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Score for this dimension from 1 (poor) to 10 (excellent).",
    )


class Scores(BaseModel):
    """
    Scores for every evaluation dimension.

    Each dimension contains both:
    1. An observation explaining what the evaluator found.
    2. A numerical score based on that observation.
    """

    hook: DimensionScore
    clarity: DimensionScore
    engagement: DimensionScore
    authenticity: DimensionScore
    professionalism: DimensionScore
    structure: DimensionScore
    faithfulness: DimensionScore


class ImprovementOpportunity(BaseModel):
    category: str = Field(..., description="E.g., Hook, Engagement, Conciseness, Structure")
    priority: Literal["Low", "Medium", "High", "Critical"] = Field(..., description="Priority level of the improvement")
    reason: str = Field(..., description="Explanation of what to improve and why it matters")
    recommendation: str = Field(..., description="High-level recommendation without rewriting the text")

class EvaluationResult(BaseModel):
    scores: Scores = Field(..., description="Multi-dimensional scoring of the LinkedIn post.")

    strengths: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="Exactly 3 things that are already working well in the post."
    )

    weaknesses: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="Up to 3 meaningful issues. Return fewer, or none, if the post genuinely has none.",
    )

    improvement_opportunities: List[ImprovementOpportunity] = Field(
        default_factory=list,
        min_length=2,
        description="Actionable improvements. Empty if no meaningful improvement remains.",
    )

    feedback: str = Field(
        ...,
        description="Concise 2-4 sentence overall assessment and actionable feedback."
    )

    unsupported_claims: List[str] = Field(
    default_factory=list,
    description=(
        "Verbatim snippets from the post that are not supported by the brief. "
        "Empty list if everything traces back to the brief."
    ),
    )

