from pydantic import BaseModel, Field


class NotionIngestRequest(BaseModel):
    title: str
    content: str
    source_url: str = Field(..., max_length=2048)
    allowed_roles: list[str] = Field(default_factory=lambda: ["founder", "admin", "member"])


class StripeIngestRequest(BaseModel):
    metric: str = Field(..., max_length=128)
    value: str
    allowed_roles: list[str] = Field(default_factory=lambda: ["founder", "admin", "member"])
