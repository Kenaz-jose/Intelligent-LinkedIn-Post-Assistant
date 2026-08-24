from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from src.utils.logger import logger
from src.agents.generator import GeneratorAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.reflection import ReflectionAgent
from src.agents.refiner import RefinerAgent
from src.schemas.perspective import PerspectiveBrief
from src.evaluation.policy import Decision,Verdict,judge,decide,is_better,MAX_ITERATIONS

class LinkedInState(TypedDict):
    topic: str
    brief: dict
    post: str

    evaluation: Optional[object]
    reflection: Optional[object]

    verdict: Optional[object]
    decision: Optional[object]

    iteration: int
    repairs_used: int

    current_craft: float
    previous_craft: float

    best_post: str
    best_verdict: Optional[object]
    best_evaluation: Optional[object]
    best_iteration: int

generator_agent = GeneratorAgent()
evaluator_agent = EvaluatorAgent()
reflection_agent = ReflectionAgent()
refiner_agent = RefinerAgent()

def brief_block(state: LinkedInState) -> str:
    """
    The author's brief as prompt text.

    Every agent that used to receive state["topic"] now receives this.
    One function means generator, evaluator, reflection and refiner all
    see identical source material - which is what makes the faithfulness
    score meaningful.
    """
    return PerspectiveBrief.model_validate(state["brief"]).to_prompt_block()

def generate_node(state: LinkedInState):
    post = generator_agent.invoke(brief_block(state))

    print("\n===== GENERATED POST =====")
    print(post)

    logger.info("Generated initial post")
    logger.info(post)

    return {
        "post": post,
        "iteration": 0,
        "repairs_used": 0,
        "current_craft": 0.0,
        "previous_craft": -1.0,
        "best_post": "",
        "best_verdict": None,
        "best_evaluation": None,
        "best_iteration": 0,
    }

def display_evaluation(evaluation, verdict: Verdict, decision: Decision):
    scores = evaluation.scores

    print("\n" + "=" * 60)
    print("EVALUATION REPORT")
    print("=" * 60)

    print("\nSCORES")
    print("-" * 60)

    for dim in (
        "hook",
        "clarity",
        "engagement",
        "authenticity",
        "professionalism",
        "structure",
    ):
        d = getattr(scores, dim)
        print(f"{dim.title():<16}: {d.score}/10")
        print(f"{'':<16}  {d.observation}")

    print(f"{'Faithfulness':<16}: {verdict.faithfulness}/10")
    print(f"{'':<16}  {scores.faithfulness.observation}")

    print("\nCRAFT SCORE")
    print("-" * 60)
    print(f"Weighted craft  : {verdict.craft_score}/10")

    print("\nFAITHFULNESS GATE")
    print("-" * 60)
    print(f"Faithfulness    : {verdict.faithfulness}/10")
    print(f"Gate            : {'PASS' if verdict.passes_faithfulness else 'FAIL'}")

    claims = getattr(evaluation, "unsupported_claims", [])
    if claims:
        print("\nUNSUPPORTED CLAIMS")
        print("-" * 60)
        for claim in claims:
            print(f"  - {claim}")

    if evaluation.improvement_opportunities:
        print("\nIMPROVEMENT OPPORTUNITIES")
        print("-" * 60)
        for i, item in enumerate(evaluation.improvement_opportunities, 1):
            print(f"\n{i}. [{item.priority} Priority] - {item.category}")
            print(f"   Why  : {item.reason}")
            print(f"   Fix  : {item.recommendation}")

    print("\nSTRENGTHS")
    print("-" * 60)
    for s in evaluation.strengths:
        print(f"  + {s}")

    if evaluation.weaknesses:
        print("\nWEAKNESSES")
        print("-" * 60)
        for w in evaluation.weaknesses:
            print(f"  - {w}")

    print("\nFEEDBACK")
    print("-" * 60)
    print(evaluation.feedback)

    print("\nPOLICY DECISION")
    print("-" * 60)
    print(f"{decision.outcome.upper()}: {decision.reason}")

    print("=" * 60)


def evaluate_node(state: LinkedInState):
    """
    Evaluator observes, policy decides, best draft is recorded.

    Best-draft recording happens here rather than on the exit path because
    only this node sees every intermediate draft. A node placed after the
    branches would only ever see the last one.
    """
    try:
        evaluation = evaluator_agent.invoke(state["post"], brief_block(state))
    except Exception as exc:
        logger.error(f"Evaluation failed: {exc}")
        print(f"\nEVALUATION FAILED: {exc}")
        return {
            "decision": Decision(
                outcome="ready",
                reason=f"Evaluation failed ({type(exc).__name__}). Returning best draft so far.",
            )
        }

    verdict = judge(evaluation)

    decision = decide(
        verdict=verdict,
        iteration=state.get("iteration", 0),
        repairs_used=state.get("repairs_used", 0),
        previous_craft=state.get("previous_craft", -1.0),
    )

    display_evaluation(evaluation, verdict, decision)

    logger.info(
        f"Evaluation | Craft={verdict.craft_score} "
        f"Faithfulness={verdict.faithfulness} "
        f"Gate={'PASS' if verdict.passes_faithfulness else 'FAIL'} "
        f"Decision={decision.outcome}"
    )

    update = {
        "evaluation": evaluation,
        "verdict": verdict,
        "decision": decision,
        "current_craft": verdict.craft_score,
    }

    if decision.repair_mode:
        update["repairs_used"] = state.get("repairs_used", 0) + 1

    incumbent = state.get("best_verdict")

    if is_better(verdict, incumbent):
        previous = incumbent.craft_score if incumbent else None
        print(f"\nNEW BEST DRAFT - craft {verdict.craft_score} (previous: {previous})")

        update["best_post"] = state["post"]
        update["best_verdict"] = verdict
        update["best_evaluation"] = evaluation
        update["best_iteration"] = state.get("iteration", 0)
    else:
        print(
            f"\nDraft not an improvement - keeping iteration "
            f"{state.get('best_iteration', 0)} (craft {incumbent.craft_score})"
        )

    return update

def display_reflection(reflection, repair_mode: bool):
    print("\n" + "=" * 60)
    print("REPAIR PLAN" if repair_mode else "REFLECTION PLAN")
    print("=" * 60)

    if reflection.priority_issues:
        print("\nPRIORITY ISSUES")
        print("-" * 60)
        for i, issue in enumerate(reflection.priority_issues, 1):
            print(f"{i}. {issue}")

    if reflection.strengths_to_preserve:
        print("\nSTRENGTHS TO PRESERVE")
        print("-" * 60)
        for s in reflection.strengths_to_preserve:
            print(f"  + {s}")

    print("\nOPERATIONS")
    print("-" * 60)
    if not reflection.operations:
        print("No operations required.")
    else:
        for i, op in enumerate(reflection.operations, 1):
            print(f"\n{i}. {op.op}")
            print(f"   Target Snippet : \"{op.target_snippet}\"")
            print(f"   Instruction    : {op.instruction}")

    print("=" * 60)


def reflect_node(state: LinkedInState):
    repair_mode = state["decision"].repair_mode

    try:
        reflection = reflection_agent.invoke(
            state["post"],
            state["evaluation"],
            brief_block(state),
            repair_mode=repair_mode,
        )
    except Exception as exc:
        # A parser failure must not destroy the run. Returning no operations
        # routes to finalize, which still emits the best draft recorded so far.
        logger.error(f"Reflection failed: {exc}")
        print(f"\nREFLECTION FAILED: {exc} - stopping with best draft.")
        return {
            "reflection": None,
            "decision": Decision(
                outcome="ready",
                reason=f"Reflection failed ({type(exc).__name__}). Returning best draft.",
            ),
        }

    display_reflection(reflection, repair_mode)

    logger.info(
        f"Reflection | Mode={'repair' if repair_mode else 'craft'} "
        f"Operations={len(reflection.operations)}"
    )

    for op in reflection.operations:
        logger.info(f"Operation={op.op} TargetSnippet={op.target_snippet}")

    update = {"reflection": reflection}

    if not reflection.operations:
        update["decision"] = Decision(
            outcome="ready",
            reason="Reflection found no edit worth making. Returning the current draft.",
        )

    return update

def display_refiner(refined):
    print("\n" + "=" * 60)
    print("REFINED POST")
    print("=" * 60)

    print("\nFINAL POST\n")
    print(refined.final_post)

    print("\nCHANGES APPLIED")
    print("-" * 60)
    if not refined.changes_applied:
        print("No changes were applied.")
    else:
        for i, change in enumerate(refined.changes_applied, 1):
            print(f"\n{i}. {change.op} (Status: {change.status})")
            print(f"   Target Snippet : \"{change.target_snippet}\"")
            print(f"   Reason         : {change.reason}")

    if refined.skipped_operations:
        print("\nSKIPPED OPERATIONS")
        print("-" * 60)
        for i, change in enumerate(refined.skipped_operations, 1):
            print(f"\n{i}. {change.op}")
            print(f"   Target Snippet : \"{change.target_snippet}\"")
            print(f"   Reason Skipped : {change.reason}")

    print("\nFAITHFULNESS CHECK")
    print("-" * 60)
    print(f"Passed: {refined.faithfulness_check.passed}")

    if refined.faithfulness_check.notes:
        print(f"Notes: {refined.faithfulness_check.notes}")

    print("=" * 60)


def refine_node(state: LinkedInState):
    try:
        refined = refiner_agent.invoke(
            state["post"],
            state["reflection"],
            brief_block(state),
        )
    except Exception as exc:
        logger.error(f"Refinement failed: {exc}")
        print(f"\nREFINEMENT FAILED: {exc} - keeping current draft.")
        # Burn the iteration so the loop still terminates.
        return {"iteration": state["iteration"] + 1}

    display_refiner(refined)

    logger.info(f"Refinement #{state['iteration'] + 1}")

    return {
        "post": refined.final_post,
        "iteration": state["iteration"] + 1,
        "previous_craft": state["current_craft"],
    }


def route_after_evaluation(state: LinkedInState) -> str:
    """
    Pure lookup. Every judgment was already made by the policy engine in
    evaluate_node - this only translates an outcome into an edge, so there
    is nowhere here for a second, conflicting decision to creep in.
    """
    decision = state["decision"]
    iteration = state.get("iteration", 0)

    print(f"\n[ROUTER] Iteration {iteration}/{MAX_ITERATIONS} -> {decision.outcome.upper()}")
    print(f"   {decision.reason}")

    if decision.outcome == "refine":
        return "refine"

    return "stop"


def route_after_reflection(state: LinkedInState) -> str:
    reflection = state.get("reflection")

    if reflection is None or not reflection.operations:
        print("\n[ROUTER] No operations produced -> finalize")
        return "stop"

    print(f"\n[ROUTER] {len(reflection.operations)} operation(s) -> refine")
    return "refine"

def finalize_node(state: LinkedInState):
    """
    Swap the best draft back into `post` before the graph exits.

    Refinement is allowed to explore and fail, because this node guarantees
    the caller receives the highest-scoring version, not whichever version
    happened to be last.
    """
    best_post = state.get("best_post") or state["post"]
    best_verdict = state.get("best_verdict")
    best_iteration = state.get("best_iteration", 0)
    total_iterations = state.get("iteration", 0)
    decision = state.get("decision")

    print("\n" + "=" * 60)
    print("FINAL POST")
    print("=" * 60)

    if decision is not None:
        if best_verdict is not None and best_iteration < total_iterations:
            # The decision describes the LAST draft evaluated. When an earlier
            # draft won, reporting that reason alone contradicts the verdict
            # shown beside it.
            print(f"\nStopped after iteration {total_iterations}: {decision.reason}")
            print(f"Returning iteration {best_iteration}, which scored higher.")
        else:
            print(f"\nStopped because: {decision.reason}")

    if best_verdict is not None:
        print(
            f"Best draft: iteration {best_iteration} of {total_iterations} "
            f"(craft {best_verdict.craft_score}, faithfulness {best_verdict.faithfulness})"
        )

        if not best_verdict.passes_faithfulness:
            print(
                "\nWARNING: No draft passed the faithfulness gate. The post below "
                "contains material not supported by the brief and should not be "
                "published without review. This usually means the brief was too "
                "thin to write from."
            )

        if best_iteration < total_iterations:
            print("\nNote: refinement did not improve on this draft - returning the earlier version.")

    print()
    print(best_post)
    print("=" * 60)

    logger.info(
        f"Final | BestIteration={best_iteration}/{total_iterations} "
        f"Craft={best_verdict.craft_score if best_verdict else 'n/a'} "
        f"FaithfulnessGate={'PASS' if best_verdict and best_verdict.passes_faithfulness else 'FAIL'}"
    )

    return {
        "post": best_post,
        "evaluation": state.get("best_evaluation") or state.get("evaluation"),
        "verdict": best_verdict,
    }

graph = StateGraph(LinkedInState)

graph.add_node("generate", generate_node)
graph.add_node("evaluate", evaluate_node)
graph.add_node("reflect", reflect_node)
graph.add_node("refine", refine_node)
graph.add_node("finalize", finalize_node)

graph.set_entry_point("generate")

graph.add_edge("generate", "evaluate")

graph.add_conditional_edges(
    "evaluate",
    route_after_evaluation,
    {
        "refine": "reflect",
        "stop": "finalize",
    },
)

graph.add_conditional_edges(
    "reflect",
    route_after_reflection,
    {
        "refine": "refine",
        "stop": "finalize",
    },
)

graph.add_edge("refine", "evaluate")
graph.add_edge("finalize", END)

app = graph.compile()