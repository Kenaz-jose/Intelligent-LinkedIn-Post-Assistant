import os
from typing import Any, Dict, List
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.prompts.generator import GENERATOR_PROMPT

load_dotenv(override=True)

def format_external_references(references: List[Dict[str, str]]) -> str:
    """Helper to convert structured references into a readable prompt block."""
    if not references:
        return "None provided by the author."
    
    formatted = []
    for i, ref in enumerate(references, 1):
        title = ref.get("title", "Untitled Reference")
        url = ref.get("url", "")
        snippet = ref.get("snippet", "")
        formatted.append(f"Source {i}:\n- Title: {title}\n- URL: {url}\n- Context: {snippet}")
    
    return "\n\n".join(formatted)

class GeneratorAgent:
    def __init__(
        self,
        model_name: str = "meta/llama-3.2-11b-vision-instruct",
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

    def invoke(self, payload: Dict[str, Any]) -> str:
        # Extract and format references if present in state/payload
        raw_references = payload.get("external_references", [])
        formatted_references = format_external_references(raw_references)

        response = self.chain.invoke({
            "brief": payload.get("brief", ""),
            "tone": payload.get("tone", "Professional"),
            "external_references": formatted_references,
        })
        
        return response.strip()