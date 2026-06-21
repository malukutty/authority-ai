from pydantic import BaseModel

from app.schemas.knowledge_item import KnowledgeItemRead


class SeedResponse(BaseModel):
    count_created: int
    count_skipped: int
    relationships_created: int = 0
    relationships_skipped: int = 0


class ResetDemoResponse(BaseModel):
    relationships_deleted: int
    items_deleted: int
    items_created: int
    relationships_created: int


class CleanDemoResponse(BaseModel):
    deleted_knowledge_items: int
    deleted_relationships: int
    created_knowledge_items: int
    created_relationships: int


class ConflictTestResponse(BaseModel):
    created_or_updated: list[KnowledgeItemRead]
