import os
from typing import TypedDict, Optional, List, Dict

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from tavily import TavilyClient

from src.utils.logger import logger
from src.schemas.perspective import PerspectiveBrief
from src.evaluation.policy import Decision, Verdict, judge, decide, is_better, MAX_ITERATIONS

from src.agents.hook import HookAgent
from src.agents.generator import GeneratorAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.router import RouterAgent
from src.agents.fact_checker import FactCheckerAgent
from src.agents.hook_copywriter import HookCopywriterAgent
from src.agents.stylist import StylistAgent

load_dotenv(override=True)
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

class ReferenceItem(TypedDict):
    title: str
    url: str
    snippet: str

class LinkedInState(TypedDict):
    topic: str
    brief: dict
    post: str
    tone: str
    alternative_hooks: List[Dict[str, str]]
    external_references: List[ReferenceItem]

    evaluation: Optional[object]
    verdict: Optional[object]
    decision: Optional[object]
    router_reasoning: Optional[str]

    iteration: int
    repairs_used: int

    current_craft: float
    previous_craft: float

    best_post: str
    best_alternative_hooks: List[Dict[str, str]]
    best_verdict: Optional[object]
    best_evaluation: Optional[object]
    best_iteration: int

# Initialize Agents
hook_agent = HookAgent()
generator_agent = GeneratorAgent()
evaluator_agent = EvaluatorAgent()
router_agent = RouterAgent()
fact_checker_agent = FactCheckerAgent()
hook_copywriter_agent = HookCopywriterAgent()
stylist_agent = StylistAgent()

def brief_block(state: LinkedInState) -> str:
    """The author's brief as prompt text."""
    return PerspectiveBrief.model_validate(state["brief"]).to_prompt_block()

def generate_hooks_node(state: LinkedInState) -> dict:
    hooks = hook_agent.generate_hooks(
        topic=state["topic"],
        brief=state["brief"],
        tone=state["tone"]
    )
    return {"alternative_hooks": hooks}

def generate_node(state: LinkedInState):
    brief = brief_block(state)
    tone = state.get("tone", "Direct, punchy, and technical (like a senior engineer)")

    post = generator_agent.invoke({
        "brief": brief,
        "tone": tone
    })

    print("\n===== GENERATED POST =====")
    print(post)
    logger.info("Generated initial post")

    return {
        "post": post,
        "iteration": 0,
        "repairs_used": 0,
        "current_craft": 0.0,
        "previous_craft": -1.0,
        "best_post": post,
        "best_verdict": None,
        "best_evaluation": None,
        "best_iteration": 0,
    }

def evaluate_node(state: LinkedInState):
    alt_hooks = state.get("alternative_hooks", [])
    alt_hooks_text = "\n".join(
        [f"Hook {i+1} ({h['angle']}): {h['text']}" for i, h in enumerate(alt_hooks)]
    ) if alt_hooks else "None provided."

    try:
        evaluation = evaluator_agent.invoke(
            post=state["post"],
            brief=brief_block(state),
            alternative_hooks=alt_hooks_text
        )
    except Exception as exc:
        logger.error(f"Evaluation failed: {exc}")
        return {
            "decision": Decision(outcome="ready", reason=f"Evaluation failed. Returning best draft so far.")
        }

    # Filter unfaithful alternative hooks
    valid_hooks = []
    if alt_hooks and getattr(evaluation, "hook_evaluations", None):
        for hook, eval_result in zip(alt_hooks, evaluation.hook_evaluations):
            if eval_result.is_faithful:
                valid_hooks.append(hook)
    else:
        valid_hooks = alt_hooks

    verdict = judge(evaluation)
    decision = decide(
        verdict=verdict,
        iteration=state.get("iteration", 0),
        repairs_used=state.get("repairs_used", 0),
        previous_craft=state.get("previous_craft", -1.0),
    )

    update = {
        "evaluation": evaluation,
        "verdict": verdict,
        "decision": decision,
        "current_craft": verdict.craft_score,
        "alternative_hooks": valid_hooks,
    }

    if decision.repair_mode:
        update["repairs_used"] = state.get("repairs_used", 0) + 1

    incumbent = state.get("best_verdict")

    if is_better(verdict, incumbent):
        print(f"\nNEW BEST DRAFT - craft {verdict.craft_score}")
        update.update({
            "best_post": state["post"],
            "best_verdict": verdict,
            "best_evaluation": evaluation,
            "best_iteration": state.get("iteration", 0),
            "best_alternative_hooks": valid_hooks
        })
    else:
        print(f"\nDraft not an improvement - keeping iteration {state.get('best_iteration', 0)}")

    return update

def _get_critique_string(evaluation) -> str:
    critique_items = []
    if evaluation:
        if getattr(evaluation, "feedback", None):
            critique_items.append(f"Feedback: {evaluation.feedback}")
        if getattr(evaluation, "weaknesses", None):
            critique_items.append(f"Weaknesses: {', '.join(evaluation.weaknesses)}")
        if getattr(evaluation, "unsupported_claims", None):
            critique_items.append(f"Unsupported Claims: {', '.join(evaluation.unsupported_claims)}")
    return "\n".join(critique_items) if critique_items else "Draft needs improvement."

def fix_facts_node(state: LinkedInState):
    print("\n[REPAIR] Routing to FactCheckerAgent...")
    critique = _get_critique_string(state.get("evaluation"))
    repaired_post = fact_checker_agent.invoke(state["post"], brief_block(state), critique)
    return {"post": repaired_post, "iteration": state["iteration"] + 1, "previous_craft": state["current_craft"]}

def fix_hook_node(state: LinkedInState):
    print("\n[REPAIR] Routing to HookCopywriterAgent...")
    critique = _get_critique_string(state.get("evaluation"))
    repaired_post = hook_copywriter_agent.invoke(state["post"], critique)
    return {"post": repaired_post, "iteration": state["iteration"] + 1, "previous_craft": state["current_craft"]}

def fix_flow_node(state: LinkedInState):
    print("\n[REPAIR] Routing to StylistAgent...")
    critique = _get_critique_string(state.get("evaluation"))
    repaired_post = stylist_agent.invoke(state["post"], critique)
    return {"post": repaired_post, "iteration": state["iteration"] + 1, "previous_craft": state["current_craft"]}

def dynamic_switchboard(state: LinkedInState) -> str:
    iteration = state.get("iteration", 0)
    decision = state.get("decision")
    verdict = state.get("verdict")
    evaluation = state.get("evaluation")

    # 1. Hard Limits
    if iteration >= MAX_ITERATIONS:
        print(f"\n[SWITCHBOARD] Max iterations hit ({MAX_ITERATIONS}). Forcing stop.")
        return "finalize"

    if decision and decision.outcome == "ready":
        print("\n[SWITCHBOARD] Policy engine approved draft. Stopping.")
        return "finalize"

    # 2. Agentic Routing
    critique_str = _get_critique_string(evaluation)
    craft = verdict.craft_score if verdict else 0.0
    passes_faith = verdict.passes_faithfulness if verdict else False

    route_decision = router_agent.decide(
        brief=brief_block(state),
        post=state["post"],
        critique=critique_str,
        faithfulness_pass=passes_faith,
    )

    print(f"\n[SWITCHBOARD] Decision: {route_decision.action.upper()} | Reason: {route_decision.reasoning}")
    return route_decision.action

def finalize_node(state: LinkedInState):
    best_post = state.get("best_post") or state["post"]
    print("\n" + "=" * 60 + "\nFINAL POST\n" + "=" * 60 + f"\n{best_post}\n" + "=" * 60)
    return {
        "post": best_post,
        "evaluation": state.get("best_evaluation") or state.get("evaluation"),
        "verdict": state.get("best_verdict") or state.get("verdict"),
    }

graph = StateGraph(LinkedInState)
memory = MemorySaver()

graph.add_node("generate_hooks", generate_hooks_node)
graph.add_node("generate", generate_node)
graph.add_node("evaluate", evaluate_node)
graph.add_node("finalize", finalize_node)

graph.add_node("fix_facts", fix_facts_node)
graph.add_node("fix_hook", fix_hook_node)
graph.add_node("fix_flow", fix_flow_node)

graph.add_edge(START, "generate")
graph.add_edge(START, "generate_hooks")
graph.add_edge("generate", "evaluate")
graph.add_edge("generate_hooks", "evaluate")

graph.add_conditional_edges(
    "evaluate",
    dynamic_switchboard,
    {
        "fix_facts": "fix_facts",
        "fix_hook": "fix_hook",
        "fix_flow": "fix_flow",
        "finalize": "finalize",
    },
)

graph.add_edge("fix_facts", "evaluate")
graph.add_edge("fix_hook", "evaluate")
graph.add_edge("fix_flow", "evaluate")
graph.add_edge("finalize", END)

app = graph.compile(checkpointer=memory,interrupt_before=["finalize"])