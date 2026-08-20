import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.schemas.evaluator import EvaluationResult
from src.prompts.evaluator import EVALUATOR_PROMPT

load_dotenv()

class EvaluatorAgent:
    """
    Evaluates the quality of a LinkedIn post.
    Returns: EvaluationResult
    """
    def __init__(
        self,
        model_name: str = "meta/llama-3.1-70b-instruct",
        temperature: float = 0.1,
    ):
        self.llm = ChatNVIDIA(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("NVIDIA_API_KEY"),
            max_retries=1,
            timeout=30
        )

        # Create the JSON parser using your Pydantic schema
        self.parser = PydanticOutputParser(pydantic_object=EvaluationResult)

        # Inject formatting instructions into the prompt
        self.prompt = ChatPromptTemplate.from_template(
            EVALUATOR_PROMPT + "\n\n{format_instructions}"
        )

        # The new chain pipes output straight into the parser
        self.chain = self.prompt | self.llm | self.parser

    def invoke(self, post: str, user_prompt: str) -> EvaluationResult:
        result = self.chain.invoke({
            "post": post,
            "user_prompt": user_prompt,
            "format_instructions": self.parser.get_format_instructions()
        })
        return result