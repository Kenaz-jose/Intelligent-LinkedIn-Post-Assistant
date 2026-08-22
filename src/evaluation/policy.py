"""
Deterministic decision layer over the evaluator's judgments.

The evaluator LLM observes; this module decides. Nothing here makes a
model call, so every routing decision the graph takes is reproducible
and unit-testable offline.
"""

from dataclasses import dataclass
from typing import Literal, Optional

from src.schemas.evaluator import EvaluationResult


CRAFT_WEIGHTS = {
    "hook": 0.25,
    "authenticity": 0.25,
    "clarity": 0.20,
    "structure": 0.15,
    "engagement": 0.10,
    "professionalism": 0.05,
}

FAITHFULNESS_THRESHOLD = 7
CRAFT_THRESHOLD = 7.5

MAX_ITERATIONS = 3
MAX_FAITHFULNESS_REPAIRS = 2
MAX_REPAIR_DAMAGE = 0.5
NO_BEST_YET = -100.0

Outcome = Literal["invalid", "refine", "ready"]


@dataclass(frozen=True)
class Verdict:
    """What this draft is. Frozen: a verdict is a fact about one draft."""

    craft_score: float
    faithfulness: int
    passes_faithfulness: bool
    meets_craft_bar: bool

    @property
    def ranking_key(self) -> tuple:
        """Lexicographic ordering. Python compares tuples left to right, so
        any faithful draft outranks any unfaithful one and craft only breaks
        ties within a group — the gate stays a gate during selection, with
        no branching required."""
        return (self.passes_faithfulness, self.craft_score)


@dataclass(frozen=True)
class Decision:
    """What to do next, given the verdict and where the run stands."""

    outcome: Outcome
    reason: str
    repair_mode: bool = False


def craft_score(evaluation: EvaluationResult) -> float:
    scores = evaluation.scores
    return round(sum(getattr(scores, dim).score * w for dim, w in CRAFT_WEIGHTS.items()), 2)


def judge(evaluation: EvaluationResult) -> Verdict:
    craft = craft_score(evaluation)
    faithfulness = evaluation.scores.faithfulness.score

    return Verdict(
        craft_score=craft,
        faithfulness=faithfulness,
        passes_faithfulness=faithfulness >= FAITHFULNESS_THRESHOLD,
        meets_craft_bar=craft >= CRAFT_THRESHOLD,
    )


def decide(
    verdict: Verdict,
    iteration: int,
    repairs_used: int,
    previous_craft: Optional[float] = None,
) -> Decision:
    """Faithfulness is checked before craft and before every budget, because
    a fabricating post is not a lower-quality post - it is the wrong post."""

    if not verdict.passes_faithfulness:
        if (
            repairs_used > 0
            and previous_craft is not None
            and previous_craft - verdict.craft_score > MAX_REPAIR_DAMAGE
        ):
            return Decision(
                outcome="invalid",
                reason=(
                    f"Repair reduced craft from {previous_craft} to "
                    f"{verdict.craft_score} without fixing faithfulness. "
                    f"The brief cannot support this post."
                ),
            )

        if repairs_used >= MAX_FAITHFULNESS_REPAIRS:
            return Decision(
                outcome="invalid",
                reason=(
                    f"Faithfulness {verdict.faithfulness} still below "
                    f"{FAITHFULNESS_THRESHOLD} after {repairs_used} repair "
                    f"attempts. The post cannot be grounded in this brief."
                ),
            )

        return Decision(
            outcome="refine",
            reason=(
                f"Faithfulness {verdict.faithfulness} below "
                f"{FAITHFULNESS_THRESHOLD}. Repairing invented content "
                f"(attempt {repairs_used + 1} of {MAX_FAITHFULNESS_REPAIRS})."
            ),
            repair_mode=True,
        )

    if verdict.meets_craft_bar:
        return Decision(
            outcome="ready",
            reason=f"Faithful, and craft {verdict.craft_score} clears {CRAFT_THRESHOLD}.",
        )

    if iteration >= MAX_ITERATIONS:
        return Decision(
            outcome="ready",
            reason=f"Iteration budget spent at {iteration}. Returning best draft.",
        )

    if previous_craft is not None and previous_craft >= 0 and verdict.craft_score <= previous_craft:
        return Decision(
            outcome="ready",
            reason=(
                f"Craft did not improve ({previous_craft} -> "
                f"{verdict.craft_score}). Returning best draft."
            ),
        )

    return Decision(
        outcome="refine",
        reason=f"Craft {verdict.craft_score} below {CRAFT_THRESHOLD}. Refining.",
    )


def is_better(candidate: Verdict, incumbent: Optional[Verdict]) -> bool:
    return incumbent is None or candidate.ranking_key > incumbent.ranking_key