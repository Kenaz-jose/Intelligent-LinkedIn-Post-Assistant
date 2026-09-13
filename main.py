from src.agents.workflow import app
from src.schemas.perspective import Answer
from src.utils.result_saver import save_result
from src.services.perspective_service import start_interview, probe_interview, finish_interview
from src.store.run_store import save_brief, save_run

USER_ID = "cli-user"


def run_questions(questions) -> list[Answer]:
    """Ask a list of questions and collect answers. Enter alone skips one."""
    answers = []
    for q in questions:
        print(f"\n{q.text}")
        print(f"   why : {q.why}")
        if q.placeholder:
            print(f"   e.g.: {q.placeholder}")
        answers.append(
            Answer(question_id=q.id, question_text=q.text, answer=input("   > ").strip())
        )
    return answers


def run_interview(topic: str) -> list[Answer]:
    return run_questions(start_interview(USER_ID, topic).questions)


def initial_state(topic: str, brief) -> dict:
    """
    Seed every channel in LinkedInState.

    generate_node overwrites most of these on the first tick, but seeding
    them explicitly means the state is complete from the start - which
    matters the moment a checkpointer is added, and makes a mismatch
    between this file and the workflow fail loudly here rather than
    somewhere mid-run.
    """
    return {
        "topic": topic,
        "brief": brief.model_dump(),
        "post": "",

        "evaluation": None,
        "reflection": None,
        "verdict": None,
        "decision": None,

        "iteration": 0,
        "repairs_used": 0,

        "current_craft": 0.0,
        "previous_craft": -1.0,

        "best_post": "",
        "best_verdict": None,
        "best_evaluation": None,
        "best_iteration": 0,
    }


def serializable_result(result: dict) -> dict:
    """
    Strip the frozen dataclasses out of the final state before saving.

    Verdict and Decision are plain dataclasses, not Pydantic models, so
    json.dumps cannot handle them. Their contents are flattened into
    primitives instead of being dropped, since the craft score and gate
    result are the two numbers worth keeping run to run.
    """
    verdict = result.get("verdict")
    decision = result.get("decision")
    evaluation = result.get("evaluation")

    payload = {
        "topic": result.get("topic"),
        "post": result.get("post"),
        "iterations": result.get("iteration", 0),
        "best_iteration": result.get("best_iteration", 0),
        "repairs_used": result.get("repairs_used", 0),
    }

    if verdict is not None:
        payload["craft_score"] = verdict.craft_score
        payload["faithfulness"] = verdict.faithfulness
        payload["passed_faithfulness_gate"] = verdict.passes_faithfulness

    if decision is not None:
        payload["stop_outcome"] = decision.outcome
        payload["stop_reason"] = decision.reason

    if evaluation is not None:
        payload["evaluation"] = evaluation.model_dump()

    return payload


def report(result: dict) -> None:
    verdict = result.get("verdict")
    decision = result.get("decision")

    total_drafts = result.get("iteration", 0) + 1
    best_iteration = result.get("best_iteration", 0)

    print("\n" + "=" * 60)
    print(f"FINAL POST  (best of {total_drafts} draft{'s' if total_drafts > 1 else ''})")
    print("=" * 60 + "\n")
    print(result["post"])
    print()
    print("=" * 60)

    if verdict is not None:
        print(
            f"craft {verdict.craft_score}/10 | "
            f"faithfulness {verdict.faithfulness}/10 | "
            f"gate {'PASS' if verdict.passes_faithfulness else 'FAIL'}"
        )
        print(f"winning draft: iteration {best_iteration} of {result.get('iteration', 0)}")

        if not verdict.passes_faithfulness:
            print(
                "\nWARNING: no draft passed the faithfulness gate. This post "
                "contains material not supported by your brief - review before "
                "publishing."
            )

        if best_iteration == 0 and result.get("iteration", 0) > 0:
            print(
                "\nNote: the first draft won. Refinement did not improve on it "
                "this run."
            )

    if decision is not None:
        print(f"\nstopped because: {decision.reason}")

    print("=" * 60)


def main():
    topic = input("What do you want to write about? ").strip()
    if not topic:
        print("No topic given.")
        return

    try:
        answers = run_interview(topic)
    except (KeyboardInterrupt, EOFError):
        print("\nInterview cancelled.")
        return

    if all(not a.answer for a in answers):
        print("\nNo answers given - there is nothing to ground the post in.")
        return

    was_probed = False
    probe = probe_interview(USER_ID, topic, answers)

    if probe.questions:
        print("\n" + "=" * 60)
        print("A COUPLE OF FOLLOW-UPS")
        print("=" * 60)
        print("Some answers were a little general. Press Enter to skip any.")

        try:
            probe_answers = run_questions(probe.questions)
        except (KeyboardInterrupt, EOFError):
            probe_answers = []

        if any(a.answer for a in probe_answers):
            answers = answers + probe_answers
            was_probed = True

    brief = finish_interview(USER_ID, topic, answers)

    print("\n" + "=" * 60)
    print("YOUR BRIEF")
    print("=" * 60)
    print(brief.to_prompt_block())

    if not brief.evidence:
        print(
            "\nThis brief has no first-hand experience in it. The writer would "
            "have nothing to draw on and would invent specifics, which the "
            "faithfulness check then rejects.\n"
            "Answer at least one question with something that actually "
            "happened - a project, a decision, a thing that broke."
        )
        return

    gaps = brief.thin_fields()
    if gaps:
        print("\nThe brief is usable, but these would strengthen it:")
        for g in gaps:
            print(f"  - {g}")

    brief_id = save_brief(USER_ID, brief, answers, was_probed)

    result = app.invoke(initial_state(topic, brief))

    report(result)
    save_run(brief_id, result)


if __name__ == "__main__":
    main()