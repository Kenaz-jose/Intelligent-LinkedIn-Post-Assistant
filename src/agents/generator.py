import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.prompts.generator import GENERATOR_PROMPT

load_dotenv()

class GeneratorAgent:
    def __init__(
        self,
        model_name: str = "meta/llama-3.1-70b-instruct",
        temperature: float = 0.7,
    ):
        # Use ChatNVIDIA with strict timeout and retries
        self.llm = ChatNVIDIA(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("NVIDIA_API_KEY"),
            max_retries=1,
            timeout=60
        )

        self.prompt = ChatPromptTemplate.from_template(GENERATOR_PROMPT)
        
        # Attach the StrOutputParser directly to the chain
        self.chain = self.prompt | self.llm | StrOutputParser()

    def invoke(self, brief: str) -> str:
        response = self.chain.invoke({
            "brief": brief
        })
        
        return response.strip()