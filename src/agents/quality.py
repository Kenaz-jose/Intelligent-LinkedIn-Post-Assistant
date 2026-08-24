import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.schemas.quality import AnswerAssessment
from src.prompts.quality import QUALITY_PROMPT

class AnswerQualityAgent:
    """Evaluates whether an interview response contains concrete details."""

    def __init__(
        self,
        model_name: str = "meta/llama-3.1-8b-instruct",
        temperature: float = 0.0,
    ):
        self.parser = PydanticOutputParser(pydantic_object=AnswerAssessment)
        
        self.llm = ChatNVIDIA(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("NVIDIA_API_KEY"),
            max_retries=1,
            timeout=30,
        )
        
        self.chain = (
            ChatPromptTemplate.from_template(QUALITY_PROMPT)
            | self.llm
            | self.parser
        )

    def assess(self, question: str, answer: str) -> AnswerAssessment:
        return self.chain.invoke({
            "question": question,
            "answer": answer,
            "format_instructions": self.parser.get_format_instructions(),
        })