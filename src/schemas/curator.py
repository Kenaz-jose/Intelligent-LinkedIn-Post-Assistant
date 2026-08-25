from pydantic import BaseModel, Field

class NewsCard(BaseModel):
    headline: str = Field(description="Catchy, professional headline")
    summary: str = Field(description="One sentence summary of the news")
    url: str = Field(description="Source URL")

class CuratedOptions(BaseModel):
    articles: list[NewsCard]