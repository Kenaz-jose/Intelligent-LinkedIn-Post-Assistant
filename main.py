from src.agents.workflow import app
from src.utils.result_saver import save_result


def main():

    result = app.invoke({
        "topic": "I built a LinkedIn post optimization agent using LangGraph, Ollama, and structured output models.",
        "post": "",
        "evaluation": None,
        "reflection": None,
        "iteration": 0,
        "done": False,
        "previous_hook": 0,
        "previous_engagement": 0
    })

    print("\n================ FINAL OUTPUT ================\n")
    
    print("\nIterations:", result["iteration"])

    print(result["post"])

    save_result(result)

if __name__ == "__main__":
    main()