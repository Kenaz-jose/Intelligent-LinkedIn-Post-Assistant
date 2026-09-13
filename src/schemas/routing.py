from typing import Literal
from pydantic import BaseModel, Field

class RouterDecision(BaseModel):
    """The structured decision routing the draft to the correct specialized repair agent."""
    
    reasoning: str = Field(
        description="A 1-sentence explanation identifying the most critical flaw in the draft."
    )
    action: Literal["fix_facts", "fix_hook", "fix_flow","researcher", "finalize"] = Field(
        description="Route to 'fix_facts' if faithfulness failed. Route to 'fix_hook' for a weak opening. Route to 'fix_flow' for structural/tone issues. Route to 'researcher' if missing external data/metrics. 'finalize' if ready."
    )