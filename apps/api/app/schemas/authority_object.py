from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthorityScoringBreakdown(BaseModel):
    source_authority_score: int
    extraction_confidence: int
    freshness_score: int
    completeness_score: int
    consistency_score: int


class AuthorityObject(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    domain: str
    sub_domain: str
    value: str
    source_type: str
    source_url: str
    authority: str
    confidence: str
    extraction_method: str
    last_extracted_at: datetime
    metadata: dict = Field(default_factory=dict)
    authority_score: int = 0
    scoring_breakdown: AuthorityScoringBreakdown | None = None
