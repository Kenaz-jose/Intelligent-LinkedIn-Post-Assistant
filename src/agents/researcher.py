import os
from typing import List, Dict, TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv(override=True)

class ReferenceItem(TypedDict):
    title: str
    url: str
    snippet: str

class SearchQuerySchema(BaseModel):
    query: str = Field(description="A precise, targeted search query.")

PRE_FLIGHT_PROMPT = """
You are a research assistant for technical writing.
Your job is to read the post topic and thesis, then create a single, highly-focused web search query to find current industry data, news, or benchmarks that support this thesis.

TOPIC:
{topic}

THESIS/INSTRUCTION:
{instruction}

Formulate a concise search query (max 6-8 words) that targets authoritative sources.
"""

REPAIR_PROMPT = """
You are a research assistant for technical writing.
Your job is to read the evaluator feedback and the current post topic, then create a single, highly-focused web search query to find the missing concrete metrics, data, or technical details requested.

TOPIC:
{topic}

EVALUATOR CRITIQUE:
{critique}

Formulate a concise search query (max 6-8 words) that targets authoritative sources.
"""

class ResearcherAgent:
    def __init__(self, model_name: str = "openai/gpt-oss-120b"):
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.1,
            max_retries=2,
            timeout=60.0
        )
        self.structured_llm = self.llm.with_structured_output(
            SearchQuerySchema,
            method="json_mode"
        )
        
        self.pre_flight_chain = ChatPromptTemplate.from_template(PRE_FLIGHT_PROMPT) | self.structured_llm
        self.repair_chain = ChatPromptTemplate.from_template(REPAIR_PROMPT) | self.structured_llm
        self.tavily = TavilySearchResults(max_results=3)

    def _execute_search(self, search_query: str) -> List[ReferenceItem]:
        """Helper to run Tavily and format results."""
        try:
            raw_results = self.tavily.invoke({"query": search_query})
        except Exception:
            return []

        references: List[ReferenceItem] = []
        for res in raw_results:
            references.append({
                "title": res.get("title", search_query),
                "url": res.get("url", ""),
                "snippet": res.get("content", "")[:300]
            })
        return references

    def initial_search(self, topic: str, instruction: str) -> List[ReferenceItem]:
        """Used by the FastAPI layer before the graph starts."""
        query_result = self.pre_flight_chain.invoke({
            "topic": topic,
            "instruction": instruction
        })
        return self._execute_search(query_result.query)

    def repair_search(self, topic: str, critique: str) -> List[ReferenceItem]:
        """Used by the LangGraph switchboard mid-loop to fix hallucinations."""
        query_result = self.repair_chain.invoke({
            "topic": topic,
            "critique": critique
        })
        return self._execute_search(query_result.query)