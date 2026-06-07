import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.schemas.reflection import ReflectionResult
from src.prompts.reflection import REFLECTION_PROMPT


class ReflectionAgent:
    """
    Converts evaluation results into actionable improvement plans.
    """

    def __init__(self, model_name="qwen/qwen3-4b-2507", temperature=0.2):

        self.llm = ChatOpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio",
            model=model_name,   
            temperature=temperature
        )

        self.structured_llm = self.llm.with_structured_output(ReflectionResult)

        self.prompt = ChatPromptTemplate.from_template(REFLECTION_PROMPT)

        self.chain = self.prompt | self.structured_llm  # FIX: missing pipeline

    def invoke(self, post: str, evaluation) -> ReflectionResult:
        """
        Args:
            post: original LinkedIn post
            evaluation: EvaluationResult object
        """

        return self.chain.invoke({
            "post": post,
            "evaluation": json.dumps(evaluation.model_dump(), indent=2)
        })