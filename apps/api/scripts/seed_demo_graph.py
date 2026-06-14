#!/usr/bin/env python3
"""Reset and reseed the demo knowledge graph."""

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.demo import reset_demo
from app.services.knowledge import sync_seed_allowed_roles
from app.services.source_priority import (
    ensure_allowed_roles_column,
    ensure_source_priority_column,
)

Base.metadata.create_all(bind=engine)
ensure_source_priority_column()
ensure_allowed_roles_column()
sync_seed_allowed_roles()

with SessionLocal() as db:
    result = reset_demo(db)

print(
    "Reset demo:",
    f"deleted {result.items_deleted} items, {result.relationships_deleted} relationships;",
    f"created {result.items_created} items, {result.relationships_created} relationships",
)
