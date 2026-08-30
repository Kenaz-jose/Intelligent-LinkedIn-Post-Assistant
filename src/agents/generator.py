import os
from typing import Any, Dict, List
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
#from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from src.store.vector_store import vector_store
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

def format_past_examples(past_posts: List[Dict[str, Any]]) -> str:
    """Helper to format retrieved golden samples as few-shot style references."""
    if not past_posts:
        return "No prior golden samples recorded. Follow standard high-performing LinkedIn structure."
    
    formatted = []
    for i, item in enumerate(past_posts, 1):
        topic = item.get("past_topic", "General Topic")
        post = item.get("post_text", "").strip()
        score = item.get("score", "8.0+")
        formatted.append(
            f"--- [Example {i} | Reference Score: {score}/10 | Topic: {topic}] ---\n{post}"
        )
    
    return "\n\n".join(formatted)

class GeneratorAgent:
    def __init__(
        self,
        model_name: str = "openai/gpt-oss-120b",
        temperature: float = 0.7,
    ):
        self.llm = ChatGroq(
            model=model_name,
            temperature=temperature,
            max_retries=1,
            timeout=60
        )

        self.prompt = ChatPromptTemplate.from_template(GENERATOR_PROMPT)
        self.chain = self.prompt | self.llm | StrOutputParser()

    def invoke(self, payload: Dict[str, Any]) -> str:
        # 1. Format external research references
        raw_references = payload.get("external_references", [])
        formatted_references = format_external_references(raw_references)

        # 2. Retrieve semantically similar top-scoring historical posts
        topic = payload.get("topic", "")
        past_styles = []
        if topic:
            try:
                past_styles = vector_store.get_similar_style(current_topic=topic, k=2)
            except Exception:
                past_styles = []

        formatted_examples = format_past_examples(past_styles)

        # 3. Invoke Generation Chain
        response = self.chain.invoke({
            "topic": topic,
            "brief": payload.get("brief", ""),
            "tone": payload.get("tone", "Professional"),
            "external_references": formatted_references,
            "past_examples": formatted_examples,
        })
        
        return response.strip()