import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from src.prompts.repair import FACT_CHECKER_TEMPLATE
#from src.config.settings import GEMINI_API_KEY,GEMINI_MODEL

load_dotenv(override=True)

class FactCheckerAgent:
    def __init__(self, model_name: str = "openai/gpt-oss-120b", temperature: float = 0.0):
        self.llm = ChatGroq(
            model=model_name,
            temperature=temperature,
            max_retries=1,
            timeout=30,
        )
        self.chain = FACT_CHECKER_TEMPLATE | self.llm | StrOutputParser()

    def invoke(self, post: str, brief: str, critique: str) -> str:
        try:
            return self.chain.invoke({
                "post": post,
                "brief": brief,
                "critique": critique
            })
        except Exception as exc:
            print(f"[FactCheckerAgent] Error: {exc}")
            return post