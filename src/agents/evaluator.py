from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.schemas.evaluator import EvaluationResult
from src.prompts.evaluator import EVALUATOR_PROMPT


class EvaluatorAgent:
    """
    Evaluates the quality of a LinkedIn post.

    Returns:
        EvaluationResult
    """

    def __init__(self,model_name: str = "qwen/qwen3-4b-2507",temperature: float = 0.1,):

        self.llm = ChatOpenAI(
        base_url="http://127.0.0.1:1234/v1",
        api_key="lm-studio",
        model=model_name,
        temperature=temperature
        )

        self.structured_llm = self.llm.with_structured_output(EvaluationResult)

        self.prompt = ChatPromptTemplate.from_template(EVALUATOR_PROMPT)

        self.chain = self.prompt | self.structured_llm

    def invoke(self, post: str) -> EvaluationResult:
        """
        Evaluate a LinkedIn post.

        Args:
            post (str): LinkedIn post text

        Returns:
            EvaluationResult
        """

        result = self.chain.invoke(
            {
                "post": post
            }
        )

        return result

    