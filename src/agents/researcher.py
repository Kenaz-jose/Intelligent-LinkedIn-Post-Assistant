import os
from typing import List, Dict, TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv(override=True)

# Define the schema locally to avoid circular imports from workflow.py
class ReferenceItem(TypedDict):
    title: str
    url: str
    snippet: str

class SearchQuerySchema(BaseModel):
    query: str = Field(description="A precise, targeted search query to find missing facts, benchmarks, or statistics.")

RESEARCHER_QUERY_PROMPT = """
You are a research assistant for technical writing.
Your job is to read the evaluator feedback and the current post topic, then create a single, highly-focused web search query to find the missing concrete metrics, data, or technical details requested.

TOPIC:
{topic}

EVALUATOR CRITIQUE:
{critique}

Formulate a concise search query (max 6-8 words) that targets authoritative sources or papers.
"""

class ResearcherAgent:
    def __init__(self, model_name: str = "openai/gpt-oss-120b"):
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.1,
            max_retries=2,
            timeout=30.0
        )
        self.structured_llm = self.llm.with_structured_output(
            SearchQuerySchema,
            method="json_mode"
        )
        self.prompt = ChatPromptTemplate.from_template(RESEARCHER_QUERY_PROMPT)
        self.query_chain = self.prompt | self.structured_llm
        self.tavily = TavilySearchResults(max_results=3)

    def search(self, topic: str, critique: str) -> List[ReferenceItem]:
        # 1. Generate search query
        query_result = self.query_chain.invoke({
            "topic": topic,
            "critique": critique
        })
        search_query = query_result.query

        # 2. Execute Tavily search
        try:
            raw_results = self.tavily.invoke({"query": search_query})
        except Exception:
            return []

        # 3. Format into ReferenceItem list
        references: List[ReferenceItem] = []
        for res in raw_results:
            references.append({
                "title": res.get("title", search_query),
                "url": res.get("url", ""),
                "snippet": res.get("content", "")[:300]
            })

        return references