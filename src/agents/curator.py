import os
from dotenv import load_dotenv
load_dotenv(override=True)

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from src.schemas.curator import CuratedOptions
from src.prompts.curator import curator_prompt, parser

search_tool = TavilySearchResults(max_results=3)
llm = ChatNVIDIA(model="meta/llama-3.1-70b-instruct", temperature=0.2)

# Build the explicit chain
chain = curator_prompt | llm | parser

def get_curated_topics(category: str) -> CuratedOptions:
    """Fetches trending news and curates it into structured options."""
    print(f"Fetching news for: {category}")
    
    raw_results = search_tool.invoke({"query": f"Latest breaking news and major events in {category}"})
    
    cleaned_context = "\n\n".join([
        f"Title: {res.get('title', '')}\nContent: {res.get('content', '')}\nURL: {res.get('url', '')}" 
        for res in raw_results
    ])
    
    try:
        result = chain.invoke({"category": category, "results": cleaned_context})
        print(f"Curator Success: {result}")
        return result
    except Exception as e:
        print(f"❌ Parser failed: {e}")
        # If parsing fails, invoke raw LLM output to inspect in console
        raw_output = (curator_prompt | llm).invoke({"category": category, "results": cleaned_context})
        print(f"Raw LLM Output was:\n{raw_output.content}")
        return None