import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.schemas.evaluator import EvaluationResult
from src.prompts.evaluator import EVALUATOR_PROMPT

load_dotenv(override=True)


class EvaluatorAgent:
    """
    Evaluates the quality of a LinkedIn post.
    Returns: EvaluationResult
    """

    def __init__(
        self,
        model_name: str = "meta/llama-3.2-11b-vision-instruct",
        temperature: float = 0.1,
    ):
        self.llm = ChatNVIDIA(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("NVIDIA_API_KEY"),
            max_retries=1,
            timeout=60,
        )

        self.parser = PydanticOutputParser(pydantic_object=EvaluationResult)

        self.prompt = ChatPromptTemplate.from_template(
            EVALUATOR_PROMPT + "\n\n{format_instructions}"
        )

        self.chain = self.prompt | self.llm | self.parser

    def invoke(self, post: str, brief: str, alternative_hooks: str = "None provided.") -> EvaluationResult:
        result = self.chain.invoke({
            "post": post,
            "brief": brief,
            "format_instructions": self.parser.get_format_instructions(),
            "alternative_hooks": alternative_hooks
        })
        return result