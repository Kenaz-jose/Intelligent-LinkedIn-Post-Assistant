import logging
from src.agents.brief import BriefAgent
from src.agents.interview import InterviewerAgent
from src.schemas.perspective import Answer, PerspectiveBrief, QuestionSet
from src.store.memory_store import get_memory, save_memory
from src.agents.quality import AnswerQualityAgent

logger = logging.getLogger(__name__)

_interviewer = InterviewerAgent()
_brief_agent = BriefAgent()
_quality_agent = AnswerQualityAgent()


def _get_thin_answers(answers: list[Answer]) -> list[Answer]:
    """
    Passes each answer through the SLM quality agent to determine
    if it lacks concrete evidence and requires a follow-up.
    """
    thin = []
    for item in answers:
        if not item.answer.strip():
            continue
            
        assessment = _quality_agent.assess(
            question=item.question_text, 
            answer=item.answer
        )
        
        if assessment.is_thin:
            logger.info(f"Flagged Question: '{item.question_text[:40]}...'")
            logger.info(f"SLM Reason: {assessment.reason}")

            item.slm_feedback = assessment.reason
            thin.append(item)
            
    return thin


def probe_interview(user_id: str,topic: str, answers: list[Answer], n: int = 2) -> QuestionSet:
    """
    One follow-up round on the thinnest answers.

    Runs between start_interview and finish_interview, while the answers
    can still be improved. Once the brief is synthesised the material is
    fixed, so this is the last point where a weak interview is repairable.

    Returns an empty QuestionSet when nothing needs asking. The caller
    treats "no probe needed" and "probe complete" identically, so an
    empty result is a normal outcome rather than an error.

    No user_id parameter: probing works from the answers in front of it,
    not from long-term memory. Memory shapes which questions get asked in
    the first round; this round only digs into what was already said.
    """
    
    thin = _get_thin_answers(answers)

    if not thin:
        return QuestionSet()

    return _interviewer.probe(topic, answers, thin, n=n)


def start_interview(user_id: str, topic: str, n: int = 4) -> QuestionSet:
    """
    Step 1. Called when the user submits a topic.

    Returns questions for the UI to render. Nothing is saved yet —
    the user may abandon the interview, and an abandoned interview
    should leave no trace.
    """
    memory = get_memory(user_id,topic)
    return _interviewer.invoke(
        topic=topic,
        memory_block=memory.to_prompt_block(topic),
        n=n,
    )


def finish_interview(user_id: str,topic: str,answers: list[Answer],) -> PerspectiveBrief:
    """
    Step 2. Called when the user submits their answers.

    Builds the brief, then records what was learned. Memory is only
    updated after the brief succeeds — BriefAgent raises on failure,
    so a broken run leaves memory untouched.
    """
    memory = get_memory(user_id,topic)

    brief = _brief_agent.invoke(
        topic=topic,
        answers=answers,
        memory_block=memory.to_prompt_block(topic),
    )

    save_memory(memory.absorb(brief))

    return brief