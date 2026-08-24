from pydantic import BaseModel, Field

class AnswerAssessment(BaseModel):
    is_thin: bool = Field(
        description="True if the answer is vague, generic, or lacks specific details. False if it contains concrete facts, metrics, or personal experience."
    )
    reason: str = Field(
        description="A 1-sentence explanation of why it was marked thin or concrete."
    )