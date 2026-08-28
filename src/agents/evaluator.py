import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from src.schemas.evaluator import EvaluationResult
from src.prompts.evaluator import EVALUATOR_PROMPT
#from src.config.settings import GEMINI_MODEL, GEMINI_API_KEY

load_dotenv(override=True)


class EvaluatorAgent:
    """
    Evaluates the quality of a LinkedIn post.
    Returns: EvaluationResult
    """

    def __init__(
        self,
        model_name: str = "openai/gpt-oss-120b",
        temperature: float = 0.1,
    ):
        self.llm = ChatGroq(
            model=model_name,
            temperature=temperature,
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