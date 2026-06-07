from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from src.utils.logger import logger
from src.agents.generator import GeneratorAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.reflection import ReflectionAgent
from src.agents.refiner import RefinerAgent


# STATE
class LinkedInState(TypedDict):
    topic: str
    post: str

    evaluation: Optional[object]
    reflection: Optional[object]

    iteration: int
    done: bool

    previous_hook: int
    previous_engagement: int


# AGENTS
generator = GeneratorAgent()
evaluator = EvaluatorAgent()
reflection_agent = ReflectionAgent()
refiner = RefinerAgent()

MAX_ITERATIONS = 3


# NODES
def generate_node(state: LinkedInState):
    post = generator.invoke(state["topic"])
    
    print("\n===== GENERATED POST =====")
    print(post)
    
    logger.info("Generated initial post")
    logger.info(post)

    return {
        "post": post,
        "iteration": 0,
        "previous_hook": 0,
        "previous_engagement": 0
    }


def display_evaluation(evaluation):

    scores = evaluation.scores

    print("\n" + "="*60)
    print("📊 EVALUATION REPORT")
    print("="*60)

    print("\nSCORES")
    print("-"*60)

    print(f"Hook            : {scores.hook}/10")
    print(f"Clarity         : {scores.clarity}/10")
    print(f"Engagement      : {scores.engagement}/10")
    print(f"Authenticity    : {scores.authenticity}/10")
    print(f"Professionalism : {scores.professionalism}/10")
    print(f"Structure       : {scores.structure}/10")
    print(f"Faithfulness    : {scores.faithfulness}/10")

    print("\nIMPROVEMENT PRIORITY")
    print("-"*60)

    for i, item in enumerate(evaluation.improvement_priority, 1):
        print(f"{i}. {item}")

    print("\nSTRENGTHS")
    print("-"*60)

    for s in evaluation.strengths:
        print(f"✓ {s}")

    print("\nWEAKNESSES")
    print("-"*60)

    for w in evaluation.weaknesses:
        print(f"✗ {w}")

    print("\nFEEDBACK")
    print("-"*60)
    print(evaluation.feedback)

    print("\nNeeds Improvement:", evaluation.needs_improvement)

    print("="*60)

def evaluate_node(state: LinkedInState):
    evaluation = evaluator.invoke(state["post"])
    
    display_evaluation(evaluation)
    
    logger.info(
        f"Evaluation | "
        f"Hook={evaluation.scores.hook} "
        f"Engagement={evaluation.scores.engagement} "
        f"Clarity={evaluation.scores.clarity}"
    )

    return {
        "evaluation": evaluation
    }


def display_reflection(reflection):

    print("\n" + "="*60)
    print("🧠 REFLECTION PLAN")
    print("="*60)

    print("\nPRIORITY ISSUES")
    print("-"*60)

    for i, issue in enumerate(reflection.priority_issues, 1):
        print(f"{i}. {issue}")

    print("\nSTRENGTHS TO PRESERVE")
    print("-"*60)

    for s in reflection.strengths_to_preserve:
        print(f"✓ {s}")

    print("\nOPERATIONS")
    print("-"*60)

    for i, op in enumerate(reflection.operations, 1):

        print(f"\n{i}. {op.op}")
        print(f"   Target      : {op.target}")
        print(f"   Instruction : {op.instruction}")

        if op.to_position is not None:
            print(f"   Position    : {op.to_position}")

    print("\nDONE:", reflection.done)

    print("\nCONSTRAINTS")
    print("-"*60)

    for k, v in reflection.constraints.items():
        print(f"{k}: {v}")

    print("="*60)
    
def reflect_node(state: LinkedInState):
    reflection = reflection_agent.invoke(
        state["post"],
        state["evaluation"]
    )
    
    display_reflection(reflection)
    
    logger.info(
        f"Reflection | Done={reflection.done}"
    )

    for op in reflection.operations:
        logger.info(
            f"Operation={op.op} "
            f"Target={op.target}"
        )

    return {
        "reflection": reflection,
        "done": reflection.done
    }


def display_refiner(refined):

    print("\n" + "="*60)
    print("✍️ REFINED POST")
    print("="*60)

    print("\nFINAL POST\n")
    print(refined.final_post)

    print("\nCHANGES APPLIED")
    print("-"*60)

    for i, change in enumerate(refined.changes_applied, 1):

        print(f"\n{i}. {change.op}")
        print(f"   Target      : {change.target}")
        print(f"   Description : {change.description}")

    print("\nHOOK TYPE:", refined.hook_type)

    print(
        "EXPECTED ENGAGEMENT:",
        refined.expected_engagement_level
    )

    print("\nFAITHFULNESS CHECK")
    print("-"*60)

    print(
        "Passed:",
        refined.faithfulness_check.passed
    )

    if refined.faithfulness_check.notes:
        print(
            "Notes:",
            refined.faithfulness_check.notes
        )

    print("="*60)

def refine_node(state: LinkedInState):
    refined = refiner.invoke(
        state["post"],
        state["evaluation"],
        state["reflection"]
    )
    
    display_refiner(refined)
    
    logger.info(
        f"Refinement #{state['iteration'] + 1}"
    )
    
    return {
        "post": refined.final_post,

        "iteration": state["iteration"] + 1,

        # save scores from THIS evaluation
        "previous_hook":
            state["evaluation"].scores.hook,

        "previous_engagement":
            state["evaluation"].scores.engagement
    }


# =========================
# ROUTER
# =========================

def should_continue(state: LinkedInState):

    # Reflector says stop
    if state.get("done", False):
        return "end"

    # Max iterations
    if state.get("iteration", 0) >= MAX_ITERATIONS:
        return "end"

    evaluation = state.get("evaluation")

    # Safety guard
    if evaluation is None:
        return "continue"

    # First evaluation
    if state.get("previous_hook", 0) == 0:
        return "continue"

    current_hook = evaluation.scores.hook
    current_engagement = evaluation.scores.engagement

    previous_hook = state.get("previous_hook", 0)
    previous_engagement = state.get("previous_engagement", 0)

    # No improvement
    if (
        current_hook <= previous_hook
        and current_engagement <= previous_engagement
    ):
        print("\n🛑 STOPPED: Scores no longer improving")
        return "end"

    return "continue"


# =========================
# GRAPH
# =========================

graph = StateGraph(LinkedInState)

graph.add_node("generate", generate_node)
graph.add_node("evaluate", evaluate_node)
graph.add_node("reflect", reflect_node)
graph.add_node("refine", refine_node)

graph.set_entry_point("generate")

graph.add_edge("generate", "evaluate")

graph.add_conditional_edges(
    "evaluate",
    should_continue,
    {
        "continue": "reflect",
        "end": END
    }
)

graph.add_edge("reflect", "refine")
graph.add_edge("refine", "evaluate")

app = graph.compile()