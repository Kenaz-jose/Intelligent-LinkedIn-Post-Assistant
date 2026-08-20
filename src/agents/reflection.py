import os
import json
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.schemas.reflection import ReflectionResult # Ensure you have this schema imported
from src.prompts.reflection import REFLECTION_PROMPT

load_dotenv()

class ReflectionAgent:
    def __init__(
        self,
        model_name: str = "meta/llama-3.1-70b-instruct",
        temperature: float = 0.2,
    ):
        self.llm = ChatNVIDIA(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("NVIDIA_API_KEY"),
            max_retries=1,
            timeout=30
        )

        self.parser = PydanticOutputParser(pydantic_object=ReflectionResult)
        
        self.prompt = ChatPromptTemplate.from_template(
            REFLECTION_PROMPT + "\n\n{format_instructions}"
        )
        
        self.chain = self.prompt | self.llm | self.parser

    def invoke(self, post: str, evaluation: object, topic: str) -> ReflectionResult:
        result = self.chain.invoke({
            "post": post,
            "evaluation": json.dumps(evaluation.model_dump(), indent=2),
            "user_prompt": topic,
            "format_instructions": self.parser.get_format_instructions()
        })
        return result