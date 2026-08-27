import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.schemas.routing import RouterDecision
from src.prompts.routing import ROUTER_PROMPT_TEMPLATE
#from src.config.settings import NVIDIA_MODEL, NVIDIA_API_KEY

load_dotenv(override=True)

class RouterAgent:
    """
    Managing Editor Agent that dynamically routes a draft to specialized 
    micro-agents based on the primary point of failure.
    """

    def __init__(
        self,
        model_name: str = "gemini-3.6-flash",
        temperature: float = 0.1,
    ):
        self.parser = PydanticOutputParser(pydantic_object=RouterDecision)
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("GEMINI_API_KEY"),
            max_retries=1,
            timeout=30,
        )

        # Build the chain using the imported template
        self.chain = ROUTER_PROMPT_TEMPLATE | self.llm | self.parser

    def decide(
        self,
        brief: str,
        post: str,
        critique: str,
        faithfulness_pass: bool,
    ) -> RouterDecision:
        try:
            return self.chain.invoke({
                "brief": brief,
                "post": post,
                "critique": critique,
                "faithfulness_pass": str(faithfulness_pass),
                "format_instructions": self.parser.get_format_instructions(),
            })
        except Exception as exc:
            print(f"[RouterAgent] Parsing error: {exc}. Defaulting to finalize.")
            return RouterDecision(
                reasoning="Router fallback due to parsing error.",
                action="finalize"
            )