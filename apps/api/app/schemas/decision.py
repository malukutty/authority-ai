from typing import Literal

from pydantic import BaseModel, Field


class DecisionChangeInput(BaseModel):
    domain: str = Field(..., max_length=64)
    sub_domain: str = Field(..., max_length=128)
    new_value: str


class DecisionChangeRequest(BaseModel):
    change: DecisionChangeInput


class ChangedObjectRead(BaseModel):
    domain: str
    sub_domain: str
    current_value: str
    new_value: str
    authority_score: int


class AffectedObjectRead(BaseModel):
    domain: str
    sub_domain: str
    relationship: str
    current_value: str
    authority_score: int
    source_system: str


class AuthorityUsedRead(BaseModel):
    domain: str
    sub_domain: str
    authority_score: int
    source_system: str


class LowAuthorityObjectRead(BaseModel):
    domain: str
    sub_domain: str
    current_value: str
    authority_score: int
    reason: str


DecisionReadinessStatus = Literal["ready", "needs_review", "insufficient_knowledge"]


class DecisionReadinessRead(BaseModel):
    status: DecisionReadinessStatus
    reason: str
    average_authority_score: float
    low_authority_objects: list[LowAuthorityObjectRead]


class DecisionSimulationResponse(BaseModel):
    decision: str
    changed_object: ChangedObjectRead | None = None
    affected_objects: list[AffectedObjectRead]
    recommended_checks: list[str]
    authority_used: list[AuthorityUsedRead]
    decision_readiness: DecisionReadinessRead
