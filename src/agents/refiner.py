import os
import json
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.schemas.refiner import RefinerResult
from src.prompts.refiner import REFINER_PROMPT

load_dotenv(override=True)

class RefinerAgent:
    """
    Final step: converts reflection plan into polished LinkedIn post.
    """
    def __init__(
        self,
        model_name: str = "meta/llama-3.2-11b-vision-instruct",
        temperature: float = 0.4,
    ):
        self.llm = ChatNVIDIA(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("NVIDIA_API_KEY"),
            max_retries=1,
            timeout=60
        )

        self.parser = PydanticOutputParser(pydantic_object=RefinerResult)

        self.prompt = ChatPromptTemplate.from_template(
            REFINER_PROMPT + "\n\n{format_instructions}"
        )
        
        self.chain = self.prompt | self.llm | self.parser

    def invoke(self, post: str, reflection: object, brief: str) -> RefinerResult:
        result = self.chain.invoke({
            "post": post,
            "operations": json.dumps([op.model_dump() for op in reflection.operations], indent=2),
            "brief": brief, # Critical for the faithfulness check!
            "format_instructions": self.parser.get_format_instructions()
        })
        return result