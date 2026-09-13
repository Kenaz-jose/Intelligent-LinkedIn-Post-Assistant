from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.schemas.curator import CuratedOptions

parser = PydanticOutputParser(pydantic_object=CuratedOptions)

CURATOR_SYSTEM_PROMPT = """You are an expert content curator.

Review the raw search results and select EXACTLY 3 articles.

Each article MUST contain:
- headline
- summary
- url

The final response MUST contain exactly 3 articles.
Every article MUST have all 3 fields.
Never omit the URL.

Return ONLY valid JSON matching the provided schema.
Do not include markdown.
Do not include ```json.
Do not include explanations or text outside the JSON.
Your response must begin exactly with the character {{ and end exactly with }}.
{format_instructions}
"""

curator_prompt = ChatPromptTemplate.from_messages([
    ("system", CURATOR_SYSTEM_PROMPT),
    ("user", "Category: {category}\n\nRaw Search Results:\n{results}")
]).partial(format_instructions=parser.get_format_instructions())