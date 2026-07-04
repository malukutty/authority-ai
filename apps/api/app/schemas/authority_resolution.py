from typing import Literal

from pydantic import BaseModel


ResolutionStatus = Literal["resolved", "missing_knowledge", "conflict_review"]


class CurrentTruthRead(BaseModel):
    domain: str
    sub_domain: str
    current_truth: str | None = None
    chosen_source: str | None = None
    authority_score: int
    supporting_sources: list[str]
    conflicting_sources: list[str]
    resolution_confidence: int
    resolution_status: ResolutionStatus
    resolution_reason: str
