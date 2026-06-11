from pydantic import BaseModel, ConfigDict, Field


class KnowledgeItemCreate(BaseModel):
    domain: str = Field(..., max_length=64)
    sub_domain: str = Field(..., max_length=128)
    content: str
    source_system: str = Field(default="manual", max_length=128)
    source_url: str = Field(default="", max_length=2048)
    trust_rank: int
    #allowed_roles: list[str] = Field(default=["founder", "admin", "member"])


class KnowledgeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: str
    sub_domain: str
    content: str
    source_system: str
    source_url: str
    trust_rank: int
    #allowed_roles: list[str]
