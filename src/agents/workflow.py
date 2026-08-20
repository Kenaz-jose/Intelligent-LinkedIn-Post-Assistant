from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from src.utils.logger import logger
from src.agents.generator import GeneratorAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.reflection import ReflectionAgent
from src.agents.refiner import RefinerAgent
from src.schemas.perspective import PerspectiveBrief

class LinkedInState(TypedDict):
    topic: str
    brief: dict         
    post: str

    evaluation: Optional[object]
    reflection: Optional[object]

    iteration: int
    done: bool

    previous_hook: int
    previous_engagement: int


generator = GeneratorAgent()
evaluator = EvaluatorAgent()
reflection_agent = ReflectionAgent()
refiner = RefinerAgent()

MAX_ITERATIONS = 3

def brief_block(state: LinkedInState) -> str:
    """
    The author's brief as prompt text.

    Every agent that used to receive state["topic"] now receives this.
    One function means generator, evaluator, reflection and refiner all
    see identical source material — which is what makes the faithfulness
    score meaningful.
    """
    return PerspectiveBrief.model_validate(state["brief"]).to_prompt_block()

def generate_node(state: LinkedInState):
    post = generator.invoke(brief_block(state))
    
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

    print("\nIMPROVEMENT OPPORTUNITIES")
    print("-"*60)
    for i, item in enumerate(evaluation.improvement_opportunities, 1):
        print(f"\n{i}. [{item.priority} Priority] - {item.category}")
        print(f"   Why  : {item.reason}")
        print(f"   Fix  : {item.recommendation}")

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

    print("\nNeeds Improvement:", getattr(evaluation, "needs_improvement", True))

    print("="*60)

def evaluate_node(state: LinkedInState):
    evaluation = evaluator.invoke(state["post"], brief_block(state))
    
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
    if not reflection.operations:
        print("No operations required.")
    else:
        for i, op in enumerate(reflection.operations, 1):
            print(f"\n{i}. {op.op}")
            print(f"   Target Snippet : \"{op.target_snippet}\"")
            print(f"   Instruction    : {op.instruction}")

    print(f"\nDONE: {reflection.done}")
    print("="*60)
    
def reflect_node(state: LinkedInState):
    reflection = reflection_agent.invoke(
        state["post"],
        state["evaluation"],
        brief_block(state),
    )
    
    display_reflection(reflection)
    
    logger.info(
        f"Reflection | Done={reflection.done}"
    )

    for op in reflection.operations:
        logger.info(
            f"Operation={op.op} "
            f"TargetSnippet={op.target_snippet}"
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
    if not refined.changes_applied:
        print("No changes were applied.")
    else:
        for i, change in enumerate(refined.changes_applied, 1):
            print(f"\n{i}. {change.op} (Status: {change.status})")
            print(f"   Target Snippet : \"{change.target_snippet}\"")
            print(f"   Reason         : {change.reason}")

    if refined.skipped_operations:
        print("\nSKIPPED OPERATIONS")
        print("-"*60)
        for i, change in enumerate(refined.skipped_operations, 1):
            print(f"\n{i}. {change.op}")
            print(f"   Target Snippet : \"{change.target_snippet}\"")
            print(f"   Reason Skipped : {change.reason}")

    print("\nFAITHFULNESS CHECK")
    print("-"*60)
    print(f"Passed: {refined.faithfulness_check.passed}")

    if refined.faithfulness_check.notes:
        print(f"Notes: {refined.faithfulness_check.notes}")

    print("="*60)

def refine_node(state: LinkedInState):
    refined = refiner.invoke(
        state["post"],
        state["reflection"],
        brief_block(state),
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


# ROUTER
def check_evaluation(state: LinkedInState):
    iteration = state.get("iteration", 0)
    print(f"\n🚦 [ROUTER] Checking Evaluation (Iteration {iteration}/{MAX_ITERATIONS})")

    # 1. Stop if we hit the iteration limit
    if iteration >= MAX_ITERATIONS:
        print("   🛑 STOPPED: Max iterations reached.")
        return "end"

    evaluation = state.get("evaluation")
    
    # Safety guard just in case the node failed
    if evaluation is None:
        print("   ⚠️ WARNING: No evaluation found in state. Forcing continue.")
        return "continue"

    # 2. Stop if the Evaluator says the post is already great!
    if not evaluation.needs_improvement:
        print("   ✅ STOPPED: Evaluator approved the post (needs_improvement = False).")
        return "end"

    # 3. Stop if the scores are stuck and not improving
    previous_hook = state.get("previous_hook", 0)
    previous_engagement = state.get("previous_engagement", 0)
    
    # Only check for stagnation if this isn't the first run
    if previous_hook > 0: 
        current_hook = evaluation.scores.hook
        current_engagement = evaluation.scores.engagement
        
        print(f"   📊 Trend - Hook: {previous_hook} -> {current_hook} | Engagement: {previous_engagement} -> {current_engagement}")
        
        # If the scores did not go up, stop the loop so we don't waste tokens
        if current_hook <= previous_hook and current_engagement <= previous_engagement:
            print("   🛑 STOPPED: Scores are no longer improving.")
            return "end"

    print("   ➡️ PROCEEDING: Sending to Reflection Agent...")
    return "continue"


def check_reflection(state: LinkedInState):
    print("\n🚦 [ROUTER] Checking Reflection Plan")
    
    # Stop immediately if the Reflection agent realizes no high-priority edits are needed
    if state.get("done", False):
        print("   ✅ STOPPED: Reflection agent found no high-priority edits (done = True).")
        return "end"
        
    print("   ➡️ PROCEEDING: Sending operations to Refiner Agent...")
    return "continue"

# GRAPH                                                                                                                                                                                                                                                                                                                                                                                  
graph = StateGraph(LinkedInState)

graph.add_node("generate", generate_node)
graph.add_node("evaluate", evaluate_node)
graph.add_node("reflect", reflect_node)
graph.add_node("refine", refine_node)

graph.set_entry_point("generate")

graph.add_edge("generate", "evaluate")

graph.add_conditional_edges(
    "evaluate",
    check_evaluation,
    {
        "continue": "reflect",
        "end": END
    }
)

graph.add_conditional_edges(
    "reflect",
    check_reflection,
    {
        "continue": "refine",
        "end": END
    }
)

graph.add_edge("refine", "evaluate")

app = graph.compile()