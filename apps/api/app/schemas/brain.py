from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

class KnowledgeDefinitionCreate(BaseModel):
    domain: str = Field(..., max_length=64)
    sub_domain: str = Field(..., max_length=128)
    name: str = Field(..., max_length=256)
    description: str
    source_of_truth: str = Field(..., max_length=128)
    allowed_roles: list[str]
    importance_score: int = Field(..., ge=1, le=10)


class KnowledgeDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: str
    sub_domain: str
    name: str
    description: str
    source_of_truth: str
    allowed_roles: list[str]
    importance_score: int


class BrainSubDomainRead(BaseModel):
    sub_domain: str
    source_of_truth: str


class BrainCoverageSlotRead(BaseModel):
    sub_domain: str
    name: str
    status: Literal["populated", "missing"]


class BrainCoverageResponse(BaseModel):
    coverage_percent: int
    domains: dict[str, list[BrainCoverageSlotRead]]


class BrainRecommendationRead(BaseModel):
    domain: str
    sub_domain: str
    name: str
    source_of_truth: str
    reason: str
    priority: Literal["high", "medium", "low"]


class BrainRecommendationsResponse(BaseModel):
    recommendations: list[BrainRecommendationRead]


class BrainFreshnessSlotRead(BaseModel):
    sub_domain: str
    name: str
    status: Literal["fresh", "stale", "missing"]


class BrainFreshnessResponse(BaseModel):
    brain_health_percent: int
    domains: dict[str, list[BrainFreshnessSlotRead]]


class BrainHealthPriorityRead(BaseModel):
    domain: str
    sub_domain: str
    name: str
    importance_score: int


class BrainHealthResponse(BaseModel):
    weighted_coverage_score: float
    weighted_freshness_score: float
    brain_health_score: float
    high_priority_missing: list[BrainHealthPriorityRead]
    high_priority_stale: list[BrainHealthPriorityRead]


class BrainConflictRead(BaseModel):
    domain: str
    sub_domain: str
    conflicting_sources: list[str]
    conflicting_values: list[str]
    winning_source: str


class BrainConflictsResponse(BaseModel):
    conflict_count: int
    consistency_score: float
    conflicts: list[BrainConflictRead]


class BrainLineageItemRead(BaseModel):
    domain: str
    sub_domain: str
    content: str
    source_system: str
    source_url: str
    created_at: datetime
    updated_at: datetime
    trust_rank: int
    source_priority: int


class BrainLineageResponse(BaseModel):
    domains: dict[str, list[BrainLineageItemRead]]
