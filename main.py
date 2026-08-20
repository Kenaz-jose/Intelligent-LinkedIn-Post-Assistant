from src.agents.workflow import app
from src.schemas.perspective import Answer
from src.services.perspective_service import start_interview, finish_interview
from src.utils.result_saver import save_result

USER_ID = "cli-user"


def run_interview(topic: str) -> list[Answer]:
    """Ask the questions and collect answers. Enter alone skips a question."""
    question_set = start_interview(USER_ID, topic)

    answers = []
    for q in question_set.questions:
        print(f"\n{q.text}")
        print(f"   why : {q.why}")
        if q.placeholder:
            print(f"   e.g.: {q.placeholder}")
        answers.append(
            Answer(question_id=q.id, question_text=q.text, answer=input("   > ").strip())
        )

    return answers


def main():
    topic = input("What do you want to write about? ").strip()
    if not topic:
        print("No topic given.")
        return

    answers = run_interview(topic)
    brief = finish_interview(USER_ID, topic, answers)

    print("\n" + "=" * 60)
    print("YOUR BRIEF")
    print("=" * 60)
    print(brief.to_prompt_block())

    if brief.is_thin():
        print("\n⚠️  Thin brief — the post will lean on generic material.")

    result = app.invoke({
        "topic": topic,
        "brief": brief.model_dump(),
        "post": "",
        "evaluation": None,
        "reflection": None,
        "iteration": 0,
        "done": False,
        "previous_hook": 0,
        "previous_engagement": 0,
    })

    print("\n" + "=" * 60)
    print(f"FINAL POST  (after {result['iteration']} iterations)")
    print("=" * 60 + "\n")
    print(result["post"])

    save_result(result)


if __name__ == "__main__":
    main()