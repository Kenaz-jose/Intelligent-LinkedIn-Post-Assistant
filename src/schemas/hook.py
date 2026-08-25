from pydantic import BaseModel, Field
from typing import List

class Hook(BaseModel):
    angle: str = Field(description="The psychology of the hook (e.g., Story, Contrarian, Metric)")
    text: str = Field(description="The actual 1-2 sentence hook.")

class HookVariations(BaseModel):
    hooks: List[Hook]