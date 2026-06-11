#!/usr/bin/env python3
"""One-off script to seed a knowledge item."""

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.schemas.knowledge_item import KnowledgeItemCreate
from app.services.knowledge import create_knowledge_item

Base.metadata.create_all(bind=engine)

payload = KnowledgeItemCreate(
     "domain": "financial",
  "sub_domain": "runway",
  "content": "Current runway is 14 months",
  "source_system": "manual_seed",
  "source_url": "https://example.com/finance/runway",
  "trust_rank": 1
)

with SessionLocal() as db:
    item = create_knowledge_item(db, payload)
    print(f"Created knowledge item id={item.id}")
