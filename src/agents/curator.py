import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv(override=True)

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from src.schemas.curator import CuratedOptions
from src.prompts.curator import curator_prompt, parser
#from src.config.settings import NVIDIA_MODEL, NVIDIA_API_KEY

search_tool = TavilySearchResults(max_results=3)
#llm = ChatNVIDIA(model=NVIDIA_MODEL, temperature=0.2,max_tokens=500, api_key=NVIDIA_API_KEY)

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0.2, # Keep it low for deterministic extraction
    max_retries=2
)

# This guarantees Gemini will return a validated CuratedOptions object
structured_llm = llm.with_structured_output(CuratedOptions)

# Build the explicit chain
chain = curator_prompt | llm | parser

def get_curated_topics(category: str) -> CuratedOptions:
    """Fetches trending news and curates it into structured options."""
    print(f"Fetching news for: {category}")
    
    try:
        raw_results = search_tool.invoke({"query": f"Latest breaking news and major events in {category}"})
    
        cleaned_context = "\n\n".join([
            f"Title: {res.get('title', '')}\nContent: {res.get('content', '')[:2000]}\nURL: {res.get('url', '')}" 
            for res in raw_results
        ])

        start = time.time()
        print(f"📝 Context length: {len(cleaned_context)} characters")

        result = chain.invoke({"category": category, "results": cleaned_context})
        
        # 5. Safety Fallback: Check if Gemini triggered a safety filter and returned None
        if not result:
            print("⚠️ [CuratorAgent] Model returned None. Returning empty fallback.")
            return CuratedOptions(articles=[])

        print(f"⏱️ Curator took: {time.time() - start:.2f}s")
        print(f"Curator Success: {result}")

        return result

    except Exception as e:
        print(f"❌ Parser failed: {e}")
        # If parsing fails, invoke raw LLM output to inspect in console
        #raw_output = (curator_prompt | llm).invoke({"category": category, "results": cleaned_context})
        #print(f"Raw LLM Output was:\n{raw_output.content}")
        #return None
        return CuratedOptions(articles=[])