from datetime import datetime

from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    user_role: str = "member"


class SourceRead(BaseModel):
    source_system: str
    source_url: str
    trust_rank: int
    source_priority: int
    updated_at: datetime


class AskResponse(BaseModel):
    question: str
    answer: str
    confidence: str
    sources: list[SourceRead]
    user_role: str
