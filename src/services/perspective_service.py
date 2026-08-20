from src.agents.brief import BriefAgent
from src.agents.interview import InterviewerAgent
from src.schemas.perspective import Answer, PerspectiveBrief, QuestionSet
from src.store.memory_store import get_memory, save_memory

_interviewer = InterviewerAgent()
_brief_agent = BriefAgent()


def start_interview(user_id: str, topic: str, n: int = 4) -> QuestionSet:
    """
    Step 1. Called when the user submits a topic.

    Returns questions for the UI to render. Nothing is saved yet —
    the user may abandon the interview, and an abandoned interview
    should leave no trace.
    """
    memory = get_memory(user_id)
    return _interviewer.invoke(
        topic=topic,
        memory_block=memory.to_prompt_block(),
        n=n,
    )


def finish_interview(
    user_id: str,
    topic: str,
    answers: list[Answer],
) -> PerspectiveBrief:
    """
    Step 2. Called when the user submits their answers.

    Builds the brief, then records what was learned. Memory is only
    updated after the brief succeeds — BriefAgent raises on failure,
    so a broken run leaves memory untouched.
    """
    memory = get_memory(user_id)

    brief = _brief_agent.invoke(
        topic=topic,
        answers=answers,
        memory_block=memory.to_prompt_block(),
    )

    save_memory(memory.absorb(brief))

    return brief