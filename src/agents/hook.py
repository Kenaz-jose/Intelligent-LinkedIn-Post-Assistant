import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_google_genai import ChatGoogleGenerativeAI

from src.prompts.hook import HOOK_PROMPT
from src.schemas.hook import HookVariations
#from src.config.settings import GEMINI_MODEL, GEMINI_API_KEY

load_dotenv(override=True)

def format_external_references(references: Optional[List[Dict[str, str]]]) -> str:
    if not references:
        return "None provided."
    formatted = []
    for i, ref in enumerate(references, 1):
        title = ref.get("title", "Untitled")
        snippet = ref.get("snippet", "")
        formatted.append(f"- {title}: {snippet}")
    return "\n".join(formatted)

class HookAgent:
    def __init__(self, model_name: str = "gemini-3.6-flash"):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.8,
            api_key=os.getenv("GEMINI_API_KEY"),
        ).with_structured_output(HookVariations)
        
        self.prompt = ChatPromptTemplate.from_template(HOOK_PROMPT)
        self.chain = self.prompt | self.llm

    def generate_hooks(
        self,
        topic: str,
        brief: str,
        tone: str,
        external_references: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        formatted_references = format_external_references(external_references)

        result = self.chain.invoke({
            "topic": topic,
            "brief": brief,
            "tone": tone,
            "external_references": formatted_references,
        })
        
        return [{"angle": h.angle, "text": h.text} for h in result.hooks]