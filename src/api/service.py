from src.agents.workflow import app
import json

def safe(obj):
    return json.loads(json.dumps(obj, default=str))

def run_pipeline(topic: str):

    result = app.invoke({"topic": topic})

    evaluation = result["evaluation"]
    
    # FIX: Use .get() so it defaults to None if the graph stops early
    reflection = result.get("reflection") 

    scores = [
        {"metric": "Hook", "score": evaluation.scores.hook},
        {"metric": "Clarity", "score": evaluation.scores.clarity},
        {"metric": "Engagement", "score": evaluation.scores.engagement},
        {"metric": "Authenticity", "score": evaluation.scores.authenticity},
        {"metric": "Professionalism", "score": evaluation.scores.professionalism},
        {"metric": "Structure", "score": evaluation.scores.structure},
        {"metric": "Faithfulness", "score": evaluation.scores.faithfulness},
    ]

    # FIX: Safely handle the reflection object if it doesn't exist
    reflection_data = safe(reflection.model_dump()) if reflection else {}

    return {
        "post": str(result["post"]),
        "evaluation": safe(evaluation.model_dump()),
        "reflection": reflection_data,
        "iteration": int(result.get("iteration", 0)),
        "scores": scores
    }