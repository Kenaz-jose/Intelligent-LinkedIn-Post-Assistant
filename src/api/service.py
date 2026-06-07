from src.agents.workflow import app
import json


def safe(obj):
    return json.loads(json.dumps(obj, default=str))


def run_pipeline(topic: str):

    result = app.invoke({"topic": topic})

    evaluation = result["evaluation"]
    reflection = result["reflection"]

    scores = [
        {"metric": "Hook", "score": evaluation.scores.hook},
        {"metric": "Clarity", "score": evaluation.scores.clarity},
        {"metric": "Engagement", "score": evaluation.scores.engagement},
        {"metric": "Authenticity", "score": evaluation.scores.authenticity},
        {"metric": "Professionalism", "score": evaluation.scores.professionalism},
        {"metric": "Structure", "score": evaluation.scores.structure},
        {"metric": "Faithfulness", "score": evaluation.scores.faithfulness},
    ]

    return {
        "post": str(result["post"]),
        "evaluation": safe(evaluation.model_dump()),
        "reflection": safe(reflection.model_dump()),
        "iteration": int(result["iteration"]),
        "scores": scores
    }