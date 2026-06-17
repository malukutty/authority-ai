from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDefinitionCreate(BaseModel):
    domain: str = Field(..., max_length=64)
    sub_domain: str = Field(..., max_length=128)
    name: str = Field(..., max_length=256)
    description: str
    source_of_truth: str = Field(..., max_length=128)
    allowed_roles: list[str]


class KnowledgeDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: str
    sub_domain: str
    name: str
    description: str
    source_of_truth: str
    allowed_roles: list[str]


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
