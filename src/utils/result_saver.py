from pathlib import Path
from datetime import datetime
import json


def save_result(result: dict):

    # Create results folder if it doesn't exist
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    # Unique filename for every run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = results_dir / f"run_{timestamp}.json"

    evaluation = result["evaluation"]
    scores = evaluation.scores

    data = {
        "timestamp": timestamp,
        "iterations": result["iteration"],
        "final_post": result["post"],

        "scores": {
            "hook": scores.hook,
            "clarity": scores.clarity,
            "engagement": scores.engagement,
            "authenticity": scores.authenticity,
            "professionalism": scores.professionalism,
            "structure": scores.structure,
            "faithfulness": scores.faithfulness
        },

        "improvement_priority": evaluation.improvement_priority,
        "strengths": evaluation.strengths,
        "weaknesses": evaluation.weaknesses,
        "feedback": evaluation.feedback
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(f"\n💾 Result saved: {filename}")