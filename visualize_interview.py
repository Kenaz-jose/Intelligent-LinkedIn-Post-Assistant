from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. A dummy state just for the drawing
class UI_State(TypedDict):
    pass

# 2. Dummy nodes representing your Streamlit and Service functions
def streamlit_ui_topic_input(state): pass
def interviewer_agent(state): pass
def streamlit_ui_user_answers(state): pass
def probe_agent(state): pass
def synthesize_brief(state): pass

# 3. Build the graph architecture
workflow = StateGraph(UI_State)

workflow.add_node("User_Enters_Topic", streamlit_ui_topic_input)
workflow.add_node("Interviewer_Agent", interviewer_agent)
workflow.add_node("User_Answers_Questions", streamlit_ui_user_answers)
workflow.add_node("Probe_Agent", probe_agent)
workflow.add_node("Synthesize_Brief", synthesize_brief)

# 4. Map the exact flow of Phase 1
workflow.add_edge(START, "User_Enters_Topic")
workflow.add_edge("User_Enters_Topic", "Interviewer_Agent")
workflow.add_edge("Interviewer_Agent", "User_Answers_Questions")

# Create a mock conditional edge mimicking your Streamlit logic
def require_probe(state):
    return "probe_needed" # In reality, Streamlit checks if answers are too short

workflow.add_conditional_edges(
    "User_Answers_Questions",
    require_probe,
    {
        "probe_needed": "Probe_Agent",
        "sufficient": "Synthesize_Brief"
    }
)

workflow.add_edge("Probe_Agent", "User_Answers_Questions") # Loops back for new answers
workflow.add_edge("Synthesize_Brief", END) # Hands off to Phase 2 (your main graph)

app = workflow.compile()

# 5. Generate the Image
if __name__ == "__main__":
    try:
        graph_image = app.get_graph().draw_mermaid_png()
        with open("interview_architecture.png", "wb") as f:
            f.write(graph_image)
        print("✅ Interview graph visualized and saved as interview_architecture.png")
    except Exception as e:
        print(f"Error generating graph: {e}")