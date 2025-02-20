# app/schemas.py
from pydantic import BaseModel
from typing import Optional, Any

class ConversationCreate(BaseModel):
    user_id: str
    transcript: str

class Conversation(BaseModel):
    id: int
    user_id: str
    transcript: str
    analysis: Optional[Any] = None
    created_at: str

    class Config:
        orm_mode = True

class ConversationAnalysis(BaseModel):
    aspect: str
    feedback: str
    confidence_score: float
    key_moments: list
    improvement_areas: list
