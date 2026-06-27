from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
