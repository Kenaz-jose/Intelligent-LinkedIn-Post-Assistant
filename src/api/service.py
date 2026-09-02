import json
from typing import AsyncGenerator, Optional
from src.agents.workflow import app
from src.agents.workflow import Decision

def safe(obj):
    if not obj:
        return {}
    
    # If it's already a dictionary
    if isinstance(obj, dict):
        return json.loads(json.dumps(obj, default=str))
        
    # If it's a Pydantic model
    if hasattr(obj, "model_dump"):
        return json.loads(json.dumps(obj.model_dump(), default=str))
        
    # If it's a NamedTuple
    if hasattr(obj, "_asdict"):
        return json.loads(json.dumps(obj._asdict(), default=str))
        
    # If it's a Python dataclass or standard object
    if hasattr(obj, "__dict__"):
        return json.loads(json.dumps(obj.__dict__, default=str))
        
    # Ultimate fallback: wrap it in a dictionary so FastAPI doesn't crash
    return {"raw_value": str(obj)}
    
def format_state_response(thread_id: str, state_snapshot) -> dict:
    values = state_snapshot.values if state_snapshot else {}
    next_nodes = list(state_snapshot.next) if state_snapshot and state_snapshot.next else []

    status = "completed"
    if "finalize" in next_nodes:
        status = "awaiting_post_approval"
    elif "review_research" in next_nodes:
        status = "awaiting_research_review"
    elif next_nodes:
        status = "in_progress"

    evaluation = values.get("best_evaluation") or values.get("evaluation")
    verdict = values.get("best_verdict") or values.get("verdict")
    
    if values.get("human_feedback_applied"):
        response_post = values.get("post", "")
    else:
        response_post = values.get("best_post") or values.get("post", "")   
    return {
        "thread_id": thread_id,
        "post": str(response_post),
        "evaluation": safe(evaluation),
        "verdict": safe(verdict),
        "iteration": int(values.get("iteration", 0)),
        "status": status,
        "proposed_references": values.get("proposed_references", []),
        "reasoning_steps": values.get("reasoning_steps", [])
    }

async def stream_pipeline_events(thread_id: str, topic: str, brief: dict, tone: str) -> AsyncGenerator[str, None]:
    config = {"configurable": {"thread_id": thread_id}}
    input_data = {"topic": topic, "brief": brief, "tone": tone, "reasoning_steps": []}

    async for event in app.astream(input_data, config=config, stream_mode="updates"):
        for node_name, updates in event.items():
            
            if not isinstance(updates, dict):
                continue
                
            steps = updates.get("reasoning_steps", [])
            latest_step = steps[-1] if steps else f"Executing stage: {node_name}"
            
            # Extract the actual content generated during this specific node's execution
            latest_post = updates.get("post")
            latest_evaluation = updates.get("evaluation")
            
            payload = {
                "node": node_name,
                "step": latest_step,
                "thread_id": thread_id
            }
            
            # Only add post and evaluation to the payload if the node actually produced them
            if latest_post:
                payload["post"] = latest_post
            if latest_evaluation:
                payload["evaluation"] = safe(latest_evaluation)

            yield f"data: {json.dumps(payload)}\n\n"

    state = app.get_state(config)
    final_payload = format_state_response(thread_id, state)
    yield f"data: {json.dumps({'status': 'final', 'result': final_payload})}\n\n"

async def resume_pipeline(thread_id: str, feedback: Optional[str] = None, approved_references: Optional[list] = None):
    config = {"configurable": {"thread_id": thread_id}}
    state = app.get_state(config)

    if not state or not state.next:
        return format_state_response(thread_id, state)

    # 1. Handle Human Feedback on the Draft
    if feedback:
        app.update_state(
            config,
            {
                "human_feedback": feedback,
                "iteration": 0  
            },
            as_node="evaluate" 
        )
    # 2. Handle Human Approval (Only trigger if paused at evaluate and no feedback given)
    elif state.next[0] == "evaluate":
        app.update_state(
            config,
            {
                "human_feedback": None,
                "decision": {"outcome": "ready", "reason": "Manual human approval"} # Must be "ready" to match your switchboard
            },
            as_node="evaluate"
        )

    # 3. Handle External Research Approval
    if approved_references is not None:
        app.update_state(
            config,
            {
                "external_references": approved_references,
                "reasoning_steps": state.values.get("reasoning_steps", []) + [f"Approved {len(approved_references)} references."]
            },
            as_node="review_research"
        )

    await app.ainvoke(None, config=config)
    new_state = app.get_state(config)
    return format_state_response(thread_id, new_state)

def get_pipeline_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state = app.get_state(config)
    return format_state_response(thread_id, state)