import uuid
from src.agents.workflow import app, LinkedInState

def run_test():
    # 1. Define the unique thread configuration
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Setup a dummy initial state based on your LinkedInState schema
    initial_state = {
        "topic": "Why multi-agent systems are expensive",
        "brief": {
            "position": "Use linear state machines instead.",
            "audience": "Developers",
            "takeaway": "Stop burning tokens.",
            "experience": "Built a multi-agent RAG that looped infinitely.",
            "specifics": "Saved 50% cost."
        },
        "tone": "Direct, technical, and slightly contrarian", # <--- ADD THIS LINE
        "post": "",
        "iteration": 0,
        "repairs_used": 0,
        "current_craft": 0.0,
        "previous_craft": -1.0
    }

    # 2. Start the run
    print("Starting autonomous generation...")
    for event in app.stream(initial_state, config=config):
        print(f"Executed node: {list(event.keys())[0]}")

    # 3. Check if the graph is paused waiting for human input
    current_state = app.get_state(config)

    if current_state.next and current_state.next[0] == "finalize":
        print("\n" + "="*40)
        print("⏸️ HUMAN IN THE LOOP PAUSE ⏸️")
        print("="*40)
        
        state_values = current_state.values
        draft = state_values.get("best_post", state_values.get("post", "No draft found."))
        print(f"BEST DRAFT SO FAR:\n{draft}\n")
        
        # 4. Get human decision from terminal
        user_decision = input("Type 'approve' to finalize, or provide custom feedback to revise: ")
        
        if user_decision.lower() == "approve":
            print("Approved! Resuming graph to finalize...")
            app.invoke(None, config=config)
            
            final_state = app.get_state(config)
            print("\nFINAL POST:")
            print(final_state.values.get("post"))
            
        else:
            print("Revisions requested. Routing back...")
            app.update_state(
                config,
                {"evaluation": {"feedback": f"HUMAN OVERRIDE: {user_decision}"}},
                as_node="evaluate"
            )
            
            for event in app.stream(None, config=config):
                 print(f"Executed node: {list(event.keys())[0]}")

if __name__ == "__main__":
    run_test()