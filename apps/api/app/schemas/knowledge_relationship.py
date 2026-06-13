from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.knowledge_item import KnowledgeItemRead

RelationshipType = Literal["depends_on", "affects", "caused_by", "related_to"]


class KnowledgeRelationshipCreate(BaseModel):
    source_id: int
    target_id: int
    relationship_type: RelationshipType = Field(..., max_length=64)


class KnowledgeRelationshipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_knowledge_id: int
    target_knowledge_id: int
    relationship_type: str


class KnowledgeItemRelationshipsResponse(BaseModel):
    knowledge_item: KnowledgeItemRead
    relationships: list[KnowledgeRelationshipRead]
