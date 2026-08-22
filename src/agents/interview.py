import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.prompts.probe import PROBE_PROMPT
from src.prompts.interview import INTERVIEW_QUESTIONS_PROMPT
from src.schemas.perspective import InterviewQuestion, QuestionSet, Answer
from src.utils.json_output import extract_json

load_dotenv()


class InterviewerAgent:
    """
    Asks the user for their actual views on a topic.

    Unlike the Generator, this agent does not produce content.
    It produces QUESTIONS, which the user answers in the UI.

    Temperature is high (0.8) on purpose. Questions should be
    varied and surprising. A low temperature here produces the
    same four safe questions for every topic.
    """

    def __init__(
        self,
        model_name: str = "meta/llama-3.1-70b-instruct",
        temperature: float = 0.8,
    ):
        self.llm = ChatNVIDIA(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("NVIDIA_API_KEY"),
            max_retries=1,
            timeout=60,
        )

        self.prompt = ChatPromptTemplate.from_template(INTERVIEW_QUESTIONS_PROMPT)
        self.chain = self.prompt | self.llm | StrOutputParser()

        self.probe_llm = ChatNVIDIA(
            model=model_name,
            temperature=0.4,
            api_key=os.getenv("NVIDIA_API_KEY"),
            max_retries=1,
            timeout=60,
        )

        self.probe_chain = (
            ChatPromptTemplate.from_template(PROBE_PROMPT)
            | self.probe_llm
            | StrOutputParser()
        )


    @staticmethod
    def _format_answers(answers: list[Answer]) -> str:
        """Question-and-answer pairs as prompt text. Blank answers are
        marked explicitly - an unanswered question is different from a
        vague one, and the model should be able to tell them apart."""
        if not answers:
            return "(nothing answered)"

        blocks = []
        for a in answers:
            response = a.answer.strip() or "(skipped)"
            blocks.append(f"Q: {a.question_text}\nA: {response}")

        return "\n\n".join(blocks)

    def probe(
        self,
        topic: str,
        answers: list[Answer],
        thin: list[Answer],
        n: int = 2,
    ) -> QuestionSet:
        """
        One follow-up round on the thinnest answers.

        Returns an empty QuestionSet when nothing needs asking, when the
        model declines to ask, or when it fails. All three cases mean the
        same thing to the caller: move on to the brief.

        This is the opposite fallback from invoke(). A failed first round
        leaves the user with nothing, so fixed questions are better than
        none. A failed probe just means the author keeps the answers they
        already gave, and inventing questions to fill the gap would be
        worse than skipping it.
        """
        if not thin:
            return QuestionSet()

        try:
            raw = self.probe_chain.invoke({
                "topic": topic,
                "all_answers": self._format_answers(answers),
                "thin_answers": self._format_answers(thin),
                "n": n,
            })

            question_set = QuestionSet.model_validate(extract_json(raw))

            # Ids are namespaced away from q1..qn so probe answers cannot
            # collide with first-round answers when the two lists are
            # concatenated for the brief.
            for i, question in enumerate(question_set.questions[:n], start=1):
                question.id = f"p{i}"

            question_set.questions = question_set.questions[:n]
            return question_set

        except Exception as exc:
            print(f"[InterviewerAgent] probe failed: {exc}")
            return QuestionSet()

            
    def invoke(
        self,
        topic: str,
        memory_block: str = "(First interview with this person — nothing known yet)",
        n: int = 4,
    ) -> QuestionSet:
        """
        Returns a QuestionSet. Never raises.

        If the model fails to produce valid JSON twice, we fall back
        to a fixed set of questions. A weaker interview is acceptable;
        a dead-ended user is not.
        """
        for attempt in range(2):
            try:
                raw = self.chain.invoke({
                    "topic": topic,
                    "memory_block": memory_block,
                    "n": n,
                })
                question_set = QuestionSet.model_validate(extract_json(raw))

                if question_set.questions:
                    # Renumber so ids are always q1..qn regardless of what
                    # the model returned. Answers are matched on these ids.
                    for i, question in enumerate(question_set.questions[:n], start=1):
                        question.id = f"q{i}"
                    question_set.questions = question_set.questions[:n]
                    return question_set

            except Exception as exc:
                print(f"[InterviewerAgent] attempt {attempt + 1} failed: {exc}")

        return self._fallback(topic, n)

    @staticmethod
    def _fallback(topic: str, n: int) -> QuestionSet:
        """
        Fixed questions used when the model fails.

        These are deliberately the four angles the prompt asks for:
        experience, disagreement, specifics, audience.
        """
        questions = [
            InterviewQuestion(
                id="q1",
                text=f"What is the most recent thing you personally did, built or watched fail involving {topic}?",
                why="First-hand detail is what makes the post yours.",
                placeholder="We removed our orchestration layer after it added 40s per run.",
            ),
            InterviewQuestion(
                id="q2",
                text=f"What do most people in your field believe about {topic} that you think is wrong?",
                why="Disagreement is what stops people scrolling.",
                placeholder="Everyone thinks more agents means more capability. It mostly means more failure modes.",
            ),
            InterviewQuestion(
                id="q3",
                text="Which tools, numbers or timeframes would you point at to back that up?",
                why="Specifics separate credible from forgettable.",
                placeholder="Three months, two frameworks, most incidents traced to retries.",
            ),
            InterviewQuestion(
                id="q4",
                text="Who do you want reading this, and what should they do differently afterwards?",
                why="Gives the post someone to talk to and a way to end.",
                placeholder="Engineering leads about to adopt a framework. Prototype without one first.",
            ),
        ]
        return QuestionSet(questions=questions[:n])