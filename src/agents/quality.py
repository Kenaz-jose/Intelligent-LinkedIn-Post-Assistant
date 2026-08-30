import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
#from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from src.schemas.quality import AnswerAssessment
from src.prompts.quality import QUALITY_PROMPT
#from src.config.settings import NVIDIA_MODEL, NVIDIA_API_KEY

class AnswerQualityAgent:
    """Evaluates whether an interview response contains concrete details."""

    def __init__(
        self,
        model_name: str = "openai/gpt-oss-120b",
        temperature: float = 0.0,
    ):
        self.parser = PydanticOutputParser(pydantic_object=AnswerAssessment)
        
        self.llm = ChatGroq(
            model=model_name,
            temperature=temperature,
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