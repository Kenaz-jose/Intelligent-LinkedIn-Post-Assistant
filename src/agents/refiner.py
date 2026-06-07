import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.schemas.refiner import RefinerResult
from src.prompts.refiner import REFINER_PROMPT


class RefinerAgent:
    """
    Final step: converts reflection plan into polished LinkedIn post.
    """

    def __init__(
        self,
        model_name: str = "qwen/qwen3-4b-2507",
        temperature: float = 0.4,
    ):

        self.llm = ChatOpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio",
            model=model_name,
            temperature=temperature
        )

        self.structured_llm = self.llm.with_structured_output(RefinerResult)

        self.prompt = ChatPromptTemplate.from_template(REFINER_PROMPT)

    def invoke(self, post, evaluation, reflection):

        result = self.prompt.format_prompt(
            post=post,

            evaluation=json.dumps(
                evaluation.model_dump(),
                indent=2
            ),


            operations=json.dumps(
                [op.model_dump() for op in reflection.operations],
                indent=2
            )
        )

        messages = result.to_messages()

        return self.structured_llm.invoke(messages)