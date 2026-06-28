from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.authority_object import AuthorityObject
from app.schemas.knowledge_item import KnowledgeItemRead

class AnalyzeWebsiteRequest(BaseModel):
    website_url: str = Field(..., max_length=2048)


class CompanySnapshot(BaseModel):
    company_name: str
    industry: str
    product: str
    icp: str
    pricing: str
    stage: str
    employees: str
    funding: str
    website: str
    description: str


class ExtractionMetadata(BaseModel):
    source_url: str
    canonical_url: str
    confidence: str
    extraction_method: str
    fields_extracted: list[str]
    public_links: dict[str, str]


class AnalyzeWebsiteResponse(BaseModel):
    company_snapshot: CompanySnapshot
    public_knowledge_objects: int
    missing_private_fields: list[str]
    extraction_metadata: ExtractionMetadata
    authority_objects: list[AuthorityObject]


class PublicKnowledgeRequest(BaseModel):
    website_url: str = Field(..., max_length=2048)


class PublicKnowledgeResponse(BaseModel):
    website_url: str
    company_name: str
    authority_objects_count: int
    authority_objects: list[AuthorityObject]
    extraction_metadata: ExtractionMetadata


class PrivateKnowledge(BaseModel):
    current_mrr: str = ""
    current_runway: str = ""
    top_customer_objection: str = ""
    current_engineering_blocker: str = ""
    founder_dependent_knowledge: str = ""


class GenerateBrainRequest(BaseModel):
    company_snapshot: CompanySnapshot
    private_knowledge: PrivateKnowledge = Field(default_factory=PrivateKnowledge)


class GenerateBrainResponse(BaseModel):
    company_name: str
    public_knowledge_objects: int
    founder_knowledge_objects: int
    total_knowledge_objects: int
    items_created: list[KnowledgeItemRead]
    company_brain_status: str


class CurrentBrainResponse(BaseModel):
    company_name: str
    domains_populated: list[str]
    knowledge_count: int
    recommended_next_steps: list[str]


class RefreshCompanyRequest(BaseModel):
    website_url: str = Field(..., max_length=2048)


class RefreshSummaryRead(BaseModel):
    new: int
    updated: int
    removed: int
    unchanged: int


class RefreshChangeRead(BaseModel):
    type: Literal["new", "updated", "removed", "unchanged"]
    domain: str
    sub_domain: str
    before: str | None = None
    after: str | None = None


class CompanyRefreshResponse(BaseModel):
    company: str
    summary: RefreshSummaryRead
    changes: list[RefreshChangeRead]


class RefreshHistoryEntry(BaseModel):
    time: datetime
    summary: RefreshSummaryRead


class RefreshHistoryResponse(BaseModel):
    refreshes: list[RefreshHistoryEntry]
