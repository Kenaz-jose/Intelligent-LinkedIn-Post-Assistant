import os
from typing import List, Dict
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv(override=True)


def get_tavily_client() -> TavilyClient:
    """Initializes and returns the Tavily API client."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY is not set in the environment variables.")
    return TavilyClient(api_key=api_key)


def fetch_live_context(topic: str, thesis: str = "", max_results: int = 5) -> List[Dict[str, str]]:
    """
    Searches the web for recent industry data, benchmarks, or articles
    related to the post topic and core thesis.
    
    Returns a sanitized list of dictionaries matching the ReferenceItem schema.
    """
    try:
        client = get_tavily_client()
        
        # Formulate a focused search query using the topic and key thesis words
        query = f"{topic} {thesis}".strip()
        # Keep query concise (under ~15 words) for optimal search relevance
        query_words = query.split()[:15]
        clean_query = " ".join(query_words)
        
        response = client.search(
            query=clean_query,
            search_depth="basic",
            max_results=max_results,
            include_raw_content=False
        )
        
        results: List[Dict[str, str]] = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", "No Title"),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:250]  # Concise snippet for UI display
            })
            
        return results

    except Exception as e:
        print(f"⚠️ Error fetching live context from Tavily: {e}")
        return []