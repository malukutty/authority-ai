"""Authority AI knowledge architecture.

KnowledgeDefinition is the schema layer: it declares which knowledge slots exist
in the company brain (domain + sub_domain), what each slot means, which system
is the source of truth, and who may access it.

KnowledgeItem is the data layer: concrete facts ingested from systems (Stripe,
Notion, etc.) and stored as content against those same domain/sub_domain slots.

Authority AI is schema-first because the brain structure is defined before facts
flow in. Teams decide what company knowledge matters and where it lives; items
then fill those predefined slots instead of dumping unstructured documents and
hoping retrieval figures out the shape later.
"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KnowledgeDefinition(Base):
    __tablename__ = "knowledge_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sub_domain: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_of_truth: Mapped[str] = mapped_column(String(128), nullable=False)
    allowed_roles: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
