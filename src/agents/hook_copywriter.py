import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.output_parsers import StrOutputParser
from src.prompts.repair import HOOK_COPYWRITER_TEMPLATE
#from src.config.settings import NVIDIA_API_KEY,NVIDIA_MODEL
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv(override=True)

class HookCopywriterAgent:
    def __init__(self, model_name: str = "gemini-3.6-flash", temperature: float = 0.4):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("GEMINI_API_KEY"),
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