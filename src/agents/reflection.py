import os
import json
from typing import List

from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.schemas.reflection import ReflectionResult
from src.schemas.evaluator import EvaluationResult
from src.prompts.reflection import REFLECTION_PROMPT
from src.prompts.repair import REPAIR_PROMPT

load_dotenv(override=True)


class ReflectionAgent:
    """
    Turns an evaluation into a set of edit operations.

    Runs in one of two modes. Normal mode improves craft. Repair mode fires
    when the policy engine's faithfulness gate fails, and is deliberately
    narrow: it may only remove unsupported content. Mixing the two lets the
    model polish the hook of a post that invents a client story, so the
    modes are kept as separate prompts rather than one prompt with a flag.
    """

    def __init__(self, model_name: str = "meta/llama-3.2-11b-vision-instruct", temperature: float = 0.2, repair_temperature: float = 0.0):
        self.parser = PydanticOutputParser(pydantic_object=ReflectionResult)

        self.llm = ChatNVIDIA(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("NVIDIA_API_KEY"),
            max_retries=1,
            timeout=60,
        )

        # Repair is extraction, not judgment. Creativity here invents
        # replacement material, which is the failure being repaired.
        self.repair_llm = ChatNVIDIA(
            model=model_name,
            temperature=repair_temperature,
            api_key=os.getenv("NVIDIA_API_KEY"),
            max_retries=1,
            timeout=30,
        )

        self.chain = (
            ChatPromptTemplate.from_template(
                REFLECTION_PROMPT + "\n\n{format_instructions}"
            )
            | self.llm
            | self.parser
        )

        self.repair_chain = (
            ChatPromptTemplate.from_template(
                REPAIR_PROMPT + "\n\n{format_instructions}"
            )
            | self.repair_llm
            | self.parser
        )

    @staticmethod
    def _format_claims(claims: List[str]) -> str:
        if not claims:
            return "(none listed — locate the unsupported material yourself)"
        return "\n".join(f"- {claim}" for claim in claims)

    def invoke(
        self,
        post: str,
        evaluation: EvaluationResult,
        brief: str,
        repair_mode: bool = False,
    ) -> ReflectionResult:
        if repair_mode:
            return self.repair_chain.invoke({
                "post": post,
                "brief": brief,
                "faithfulness": evaluation.scores.faithfulness,
                "unsupported_claims": self._format_claims(
                    getattr(evaluation, "unsupported_claims", [])
                ),
                "format_instructions": self.parser.get_format_instructions(),
            })

        return self.chain.invoke({
            "post": post,
            "evaluation": json.dumps(evaluation.model_dump(), indent=2),
            "brief": brief,
            "format_instructions": self.parser.get_format_instructions(),
        })