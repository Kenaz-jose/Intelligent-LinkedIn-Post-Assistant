import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.output_parsers import StrOutputParser
from src.prompts.repair import HOOK_COPYWRITER_TEMPLATE
#from src.config.settings import NVIDIA_API_KEY,NVIDIA_MODEL
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv(override=True)

class HookCopywriterAgent:
    def __init__(self, model_name: str = "openai/gpt-oss-120b", temperature: float = 0.4):
        self.llm = ChatGroq(
            model=model_name,
            temperature=temperature,
            max_retries=1,
            timeout=30,
        )
        self.chain = HOOK_COPYWRITER_TEMPLATE | self.llm | StrOutputParser()

    def invoke(self, post: str, critique: str) -> str:
        try:
            return self.chain.invoke({
                "post": post,
                "critique": critique
            })
        except Exception as exc:
            print(f"[HookCopywriterAgent] Error: {exc}")
            return post