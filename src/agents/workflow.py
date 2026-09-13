import os
import operator
from pprint import pprint
from typing import TypedDict, Optional, List, Dict, Annotated

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

from src.utils.logger import logger
from src.schemas.perspective import PerspectiveBrief
from src.evaluation.policy import Decision, Verdict, judge, decide, is_better, MAX_ITERATIONS

from src.agents.hook import HookAgent
from src.agents.generator import GeneratorAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.fact_checker import FactCheckerAgent
from src.agents.hook_copywriter import HookCopywriterAgent
from src.agents.stylist import StylistAgent
from src.agents.researcher import ResearcherAgent

load_dotenv(override=True)


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
    proposed_references: List[ReferenceItem]

    human_feedback: Optional[str]
    human_feedback_applied: bool
    human_feedback_history: Annotated[List[str], operator.add]

    evaluation: Optional[object]
    verdict: Optional[object]
    decision: Optional[object]
    router_reasoning: Optional[str]
    
    reasoning_steps: List[str]
    iteration: int
    repairs_used: int

    current_craft: float
    previous_craft: float

    best_post: str
    best_alternative_hooks: List[Dict[str, str]]
    best_verdict: Optional[object]
    best_evaluation: Optional[object]
    best_iteration: int

hook_agent = HookAgent()
generator_agent = GeneratorAgent()
evaluator_agent = EvaluatorAgent()
fact_checker_agent = FactCheckerAgent()
hook_copywriter_agent = HookCopywriterAgent()
stylist_agent = StylistAgent()
research_agent = ResearcherAgent()

def brief_block(state: LinkedInState) -> str:
    """
    What it does: Takes the raw Python dictionary of your brief (thesis, key points, etc.) and converts it into a clean, formatted text string.
    Why it exists: LLMs read text, not raw JSON objects. 
    This formats your thoughts so the Generator and Evaluator can read them clearly.
    """
    return PerspectiveBrief.model_validate(state["brief"]).to_prompt_block()

def generate_hooks_node(state: LinkedInState) -> dict:
    """
    What it does: Runs at the exact same time as generate_node. 
    It calls the HookAgent to look at your brief and write 3 alternative opening lines (hooks).

    Why it exists: Hooks are the most important part of a LinkedIn post. 
    Generating them in parallel saves time (latency) and gives you options later.
    """
    hooks = hook_agent.generate_hooks(
        topic=state["topic"],
        brief=state["brief"],
        tone=state["tone"]
    )
    return {"alternative_hooks": hooks}

def generate_node(state: LinkedInState):

    """
    What it does: Hands your brief and tone to the GeneratorAgent. 
    It returns the very first draft of your LinkedIn post and sets the iteration counter to 0. 
    It also saves this initial draft as the best_post to start the incumbent tracking.

    Why it exists: This is the starting line. Without this, there is nothing to evaluate or fix.
    """
    brief = brief_block(state)
    print("\n[DEBUG] WHAT THE GENERATOR SEES:\n", brief)

    tone = state.get("tone", "Direct, punchy, and technical (like a senior engineer)")

    post = generator_agent.invoke({
        "topic": state.get("topic", ""), 
        "brief": brief,
        "tone": tone,
        "external_references": state.get("external_references", [])
    })

    print("\n===== GENERATED POST =====")
    print(post)
    logger.info("Generated post")

    current_iter = state.get("iteration", 0)

    new_reasoning = state.get("reasoning_steps", []) + ["Drafting initial post based on brief and tone."]

    return {
        "post": post,
        "iteration": current_iter + 1 if current_iter > 0 else 0,
        "repairs_used": state.get("repairs_used", 0),
        "current_craft": state.get("current_craft", 0.0),
        "previous_craft": state.get("previous_craft", -1.0),
        "best_post": state.get("best_post") or post,
        "best_verdict": state.get("best_verdict"),
        "best_evaluation": state.get("best_evaluation"),
        "best_iteration": state.get("best_iteration", 0),
        "reasoning_steps": new_reasoning 
    }

def sync_evaluation_node(state: LinkedInState):
    """
    What it does: Absolutely nothing. It returns an empty dictionary {}.

    Why it exists: LangGraph requirement. 
    Because generate and generate_hooks run in parallel, LangGraph needs a "join" node to wait for both of them to finish before moving on to the Evaluator.
    """
    return {}

def evaluate_node(state: LinkedInState):

    """
    What it does: This is the brain of your application.
    It appends any web data or human feedback to the brief so the AI knows it is "legal" truth.
    It asks the EvaluatorAgent to grade the draft on 7 dimensions (1-10) and flag hallucinations.
    It filters out any alternative hooks that hallucinate.
    The Incumbent Pattern: It compares the new score to the previous_craft score. If the new draft is better, it saves it as the best_post. If the new draft is worse, it throws it out and remembers the better one.

    Why it exists: To mathematically quantify the quality and truthfulness of the text so the system can make deterministic routing decisions.
    """
    alt_hooks = state.get("alternative_hooks", [])
    alt_hooks_text = "\n".join(
        [f"Hook {i+1} ({h['angle']}): {h['text']}" for i, h in enumerate(alt_hooks)]
    ) if alt_hooks else "None provided."

    # 1. Build the brief text block from the original brief
    brief_text = brief_block(state)
    
    # 2. Format the live web data (if any exists)
    external_refs = state.get("external_references", [])
    if external_refs:
        refs_formatted = "\n".join([
            f"- {r.get('title', 'Unknown')}: {r.get('snippet', '')}" 
            for r in external_refs
        ])
        
        # 3. Append it to the brief with a strict instruction overriding the hallucination check
        brief_text += (
            "\n\n=== EXPLICITLY PERMITTED EXTERNAL DATA ===\n"
            f"{refs_formatted}\n"
            "(CRITICAL RULE: The generator is explicitly permitted to use the facts, metrics, "
            "and statistics listed in this external data section. Do NOT flag them as unfaithful "
            "or unsupported claims.)"
        )
    
    human_feedback = state.get("human_feedback")
    if human_feedback:
        brief_text += (
            "\n\n=== HUMAN OVERRIDE (VERIFIED FACTS) ===\n"
            f"{human_feedback}\n"
            "(CRITICAL RULE: The human author explicitly requested these additions. "
            "Treat any entities, metrics, or claims in this feedback as absolute ground truth. "
            "Do NOT flag them as unsupported hallucinations.)"
        )
        
    try:
        # 4. Pass the enriched brief containing BOTH the author's thoughts and the web data
        evaluation = evaluator_agent.invoke(
            post=state["post"],
            brief=brief_text, 
            alternative_hooks=alt_hooks_text
        )
    except Exception as exc:
        print(f"\n[EVALUATOR ERROR] Evaluation failed: {exc}")
        return {
            "decision": Decision(outcome="refine", reason=f"Evaluation failed. Forcing repair. Error: {exc}")
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
    
    new_reasoning = state.get("reasoning_steps", []) + [
        f"Evaluated draft: Craft score {verdict.craft_score:.1f}, Faithfulness {verdict.passes_faithfulness}."
    ]

    update = {
        "evaluation": evaluation,
        "verdict": verdict,
        "decision": decision,
        "current_craft": verdict.craft_score,
        "alternative_hooks": valid_hooks,
        "reasoning_steps": new_reasoning 
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
    
    print("\n" + "="*50)
    print("📋 EVALUATION NODE OUTPUT:")
    print("="*50)
    
    return update

def _get_critique_string(evaluation) -> str:
    """
    What it does: Extracts the AI's feedback, weaknesses, and unsupported claims from the Evaluator's Pydantic output and squashes them into a single text summary.
    
    Why it exists: When the graph routes to a repair agent (like the Stylist), that agent needs to know exactly what to fix. This function builds their instruction manual.
    """
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
    """
    What it does: Passes the draft to the FactCheckerAgent along with the exact list of hallucinations found by the Evaluator.

    Why it exists: To surgically delete lies without rewriting the entire post and ruining the style.
    """
    print("\n[REPAIR] Routing to FactCheckerAgent...")
    critique = _get_critique_string(state.get("evaluation"))
    repaired_post = fact_checker_agent.invoke(state["post"], brief_block(state), critique)
    
    new_reasoning = state.get("reasoning_steps", []) + ["FactCheckerAgent active: Resolving unverified claims."]
    
    return {
        "post": repaired_post, 
        "iteration": state["iteration"] + 1, 
        "previous_craft": state["current_craft"],
        "reasoning_steps": new_reasoning
    }

def fix_hook_node(state: LinkedInState):

    print("\n[REPAIR] Routing to HookCopywriterAgent...")
    critique = _get_critique_string(state.get("evaluation"))
    repaired_post = hook_copywriter_agent.invoke(state["post"], critique)
    
    new_reasoning = state.get("reasoning_steps", []) + ["HookCopywriterAgent active: Refining the opening lines."]
    
    return {
        "post": repaired_post, 
        "iteration": state["iteration"] + 1, 
        "previous_craft": state["current_craft"],
        "reasoning_steps": new_reasoning
    }

def fix_flow_node(state: LinkedInState):
    """
    What it does: Passes the draft to the StylistAgent. 
    It handles two things: fixing poor writing (low craft scores) AND applying your human_feedback (like "Add LangGraph"). 
    Crucially, it sets "human_feedback": None at the end so the graph doesn't get stuck in an infinite loop.

    Why it exists: To act as the senior copy-editor and human-proxy.
    """
    print("\n[REPAIR] Routing to StylistAgent...")

    evaluation = state.get("evaluation")
    critique = _get_critique_string(evaluation)

    external_refs = state.get("external_references", [])
    if external_refs:
        ref_text = "\n".join([f"- {r.get('title')}: {r.get('snippet')}" for r in external_refs])
        critique += f"\n\nAPPROVED EXTERNAL REFERENCES TO WEAVE IN:\n{ref_text}"

    human_feedback = state.get("human_feedback")
    if human_feedback:
        critique += (
            "\n\nHUMAN REVISION REQUIREMENT:\n"
            f"{human_feedback}\n"
            "\nYou MUST follow this requirement above all other critiques."
        )

    repaired_post = stylist_agent.invoke(state["post"], critique)

    new_reasoning = state.get("reasoning_steps", []) + [
        "StylistAgent active: Refining draft based on evaluator feedback and human requirements."
    ]

    return {
        "post": repaired_post,
        "iteration": state.get("iteration", 0) + 1,
        "human_feedback_applied": True if human_feedback else state.get("human_feedback_applied", False),
        "human_feedback": None,
        "human_feedback_history": [human_feedback] if human_feedback else [],
        "reasoning_steps": new_reasoning,
    }

def research_node(state: LinkedInState):
    """
    What it does: Calls the ResearcherAgent to use the Tavily search engine to find live industry data or news that supports your thesis.

    Why it exists: To prevent the AI from making up fake statistics when the brief lacks concrete evidence.
    """
    print("\n[RESEARCH] Routing to ResearcherAgent for mid-loop web data...")
    critique = _get_critique_string(state.get("evaluation"))
    
    proposed = research_agent.repair_search(
        topic=state.get("topic", ""),
        critique=critique
    )
    print(f"[RESEARCH] Retrieved {len(proposed)} candidate references.")
    
    new_reasoning = state.get("reasoning_steps", []) + [
        "ResearcherAgent active: Fetching external data to address critique."
    ]
    
    return {
        "proposed_references": proposed,
        "reasoning_steps": new_reasoning
    }

def review_research_node(state: LinkedInState):
    """
    What it does: Another dummy node that returns {}.

    Why it exists: This acts as a physical pause button. 
    The graph stops here (interrupt_before=["review_research"]) so you can read the search results in your UI and approve or reject them before they get added to the post.
    """
    return {}

def dynamic_switchboard(state: LinkedInState) -> str:
    """
    What it does: Reads the state, the scores, and the iteration count, then returns a simple string (like "fix_flow" or "finalize").

    Why it exists: To ensure the pipeline follows strict rules: Human commands > System safety limits > Truthfulness > Writing style.
    """
    iteration = state.get("iteration", 0)
    decision = state.get("decision")
    verdict = state.get("verdict")
    
    craft = verdict.craft_score if verdict else 0.0
    previous_craft = state.get("previous_craft", 0.0)
    human_feedback = state.get("human_feedback")
    
    if human_feedback:
        print("\n[SWITCHBOARD] Human feedback detected. Routing to StylistAgent for refinement.")
        return "fix_flow"

    if decision and decision.outcome == "ready":
        print("\n[SWITCHBOARD] Policy engine approved draft. Stopping.")
        return "finalize"

    if iteration >= MAX_ITERATIONS:
        print(f"\n[SWITCHBOARD] Max iterations hit ({MAX_ITERATIONS}). Forcing stop.")
        return "finalize"

    if iteration > 1 and craft < (previous_craft - 0.2):
        print(f"\n[SWITCHBOARD] Early Stopping: Score degraded from {previous_craft} to {craft}. Reverting to best draft.")
        return "finalize"

    if verdict and not verdict.passes_faithfulness:
        print("\n[SWITCHBOARD] Decision: FIX_FACTS | Reason: Evaluator flagged unfaithful claims.")
        return "fix_facts"

    if decision and decision.outcome == "needs_research":
        print("\n[SWITCHBOARD] Decision: RESEARCH | Reason: Missing verifiable domain evidence.")
        return "review_research"

    if verdict and not verdict.meets_craft_bar:
        print("\n[SWITCHBOARD] Decision: REFINE | Reason: Craft score below threshold.")
        return "fix_flow"

    if decision and decision.outcome == "refine":
        print("\n[SWITCHBOARD] Decision: REFINE | Reason: Evaluator error or fallback refine.")
        return "fix_flow"

    print("\n[SWITCHBOARD] Draft meets all standards. Stopping.")
    return "finalize"


def finalize_node(state: LinkedInState):
    """
    What it does: The final step before stopping.
    It looks at the state and asks one question: "Did the human explicitly edit this?"
    If yes, it outputs the human's edited version.
    If no, it outputs the best_post (the highest scoring AI draft), discarding any failed repair attempts.

    Why it exists: To guarantee the user always receives the safest, highest-quality version of the text when the graph pauses at interrupt_before=["finalize"].
    """
    if state.get("human_feedback_applied"):
        final_post = state["post"]
    else:
        final_post = state.get("best_post") or state["post"]

    return {
        "post": final_post,
        "evaluation": state.get("evaluation"),
        "verdict": state.get("verdict"),
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
graph.add_node("research", research_node)
graph.add_node("review_research", review_research_node)

# Initial Parallel Edges
graph.add_node("sync_evaluation", sync_evaluation_node)
graph.add_edge(START, "generate")
graph.add_edge(START, "generate_hooks")
graph.add_edge("generate", "sync_evaluation")
graph.add_edge("generate_hooks", "sync_evaluation")

graph.add_edge("sync_evaluation", "evaluate")


# Switchboard Edges
graph.add_conditional_edges(
    "evaluate",
    dynamic_switchboard,
    {
        "fix_facts": "fix_facts",
        "fix_hook": "fix_hook",
        "fix_flow": "fix_flow",
        "research": "research",
        "finalize": "finalize",
    },
)

# Repair Loops
graph.add_edge("fix_facts", "evaluate")
graph.add_edge("fix_hook", "evaluate")
graph.add_edge("fix_flow", "evaluate")

# Research Loop (Research -> HITL Breakpoint -> Generate Draft)
graph.add_edge("research", "review_research")
#graph.add_edge("review_research", "generate")
graph.add_edge("review_research", "fix_flow")  # Allow human to refine draft after research

graph.add_edge("finalize", END)

# Interrupt before finalize and before research review
app = graph.compile(
    checkpointer=memory,
    interrupt_before=["finalize", "review_research"]
)