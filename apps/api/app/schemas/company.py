from pydantic import BaseModel, Field

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


class AnalyzeWebsiteResponse(BaseModel):
    company_snapshot: CompanySnapshot
    public_knowledge_objects: int
    missing_private_fields: list[str]


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
