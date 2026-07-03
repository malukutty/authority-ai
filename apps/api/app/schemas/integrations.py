from pydantic import BaseModel


class NotionImportResponse(BaseModel):
    pages_imported: int
    knowledge_items_created: int
    knowledge_items_updated: int
    company_brain_strengthened: bool
