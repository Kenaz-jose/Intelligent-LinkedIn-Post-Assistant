from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from src.prompts.generator import GENERATOR_PROMPT

class GeneratorAgent:

    def __init__(self, model_name: str = "llama3.2",temperature:float=0.7):
        
        self.llm = ChatOllama(model=model_name, temperature=temperature)
        self.prompt = ChatPromptTemplate.from_template(GENERATOR_PROMPT)
        self.chain = self.prompt | self.llm
    
    def invoke(self, user_prompt: str) -> str:
        """
         Generate a LinkedIn post draft.

        Args:
            user_prompt: User's topic or idea

        Returns:
            Generated LinkedIn post text
        """

        response = self.chain.invoke(
            {
                "user_prompt": user_prompt
            }
        )

        return response.content.strip()