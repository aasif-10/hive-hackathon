#backend/schemas.py
from pydantic import BaseModel, Field

class TextInput(BaseModel):
    message: str = Field(..., description="Message text to be analyzed")

class TextOutput(BaseModel):
    risk: str = Field(..., description="AI classification (e.g. 'scam', 'legitimate')")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level (0 to 1)")
    reason: str = Field(..., description="AI-generated reason for the classification")
