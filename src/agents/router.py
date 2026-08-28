import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from src.schemas.routing import RouterDecision
from src.prompts.routing import ROUTER_PROMPT_TEMPLATE

load_dotenv(override=True)

class RouterAgent:
    """
    Managing Editor Agent that dynamically routes a draft to specialized 
    micro-agents or the research pipeline based on the primary point of failure.
    """

    def __init__(
        self,
        model_name: str = "openai/gpt-oss-120b",
        temperature: float = 0.1,
    ):
        self.llm = ChatGroq(
            model=model_name,
            temperature=temperature,
            max_retries=2,
            timeout=30,
        )

        # Use json_mode structured output for reliable schema conformity
        self.structured_llm = self.llm.with_structured_output(
            RouterDecision,
            method="json_mode"
        )

        self.chain = ROUTER_PROMPT_TEMPLATE | self.structured_llm

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
                "format_instructions": "Return ONLY a valid JSON object matching the schema with 'action' and 'reasoning' keys.",
            })
        except Exception as exc:
            print(f"[RouterAgent] Routing execution error: {exc}. Defaulting to finalize.")
            return RouterDecision(
                reasoning="Router fallback due to execution/parsing error.",
                action="finalize"
            )