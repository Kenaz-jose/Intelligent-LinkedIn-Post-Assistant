from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA 
from src.schemas.hook import Hook, HookVariations
from src.prompts.hook import HOOK_PROMPT

class HookAgent:
    def __init__(self, model_name="meta/llama-3.1-70b-instruct"):
        # Bind the Pydantic schema so the LLM outputs perfect JSON
        self.llm = ChatNVIDIA(model=model_name, temperature=0.8).with_structured_output(HookVariations)
        self.prompt = ChatPromptTemplate.from_template(HOOK_PROMPT)
        self.chain = self.prompt | self.llm

    def generate_hooks(self, topic: str, brief: str, tone: str) -> list[dict]:
        result = self.chain.invoke({
            "topic": topic,
            "brief": brief,
            "tone": tone
        })
        # Convert Pydantic objects to standard dictionaries for the graph state
        return [{"angle": h.angle, "text": h.text} for h in result.hooks]