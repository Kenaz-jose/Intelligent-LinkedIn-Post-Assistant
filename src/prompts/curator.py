from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.schemas.curator import CuratedOptions

parser = PydanticOutputParser(pydantic_object=CuratedOptions)

CURATOR_SYSTEM_PROMPT = """You are an expert content curator.
Review the raw search results and format them into exactly 3 compelling article summaries.

{format_instructions}
"""

curator_prompt = ChatPromptTemplate.from_messages([
    ("system", CURATOR_SYSTEM_PROMPT),
    ("user", "Category: {category}\n\nRaw Search Results:\n{results}")
]).partial(format_instructions=parser.get_format_instructions())