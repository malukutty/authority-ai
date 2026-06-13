from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.models.knowledge_relationship import KnowledgeRelationship
from app.schemas.seed import ResetDemoResponse
from app.services.knowledge import SEED_ITEMS
from app.services.source_priority import get_source_priority

PRICING_DECISION_CONTENT = (
    "We decided to price Authority AI at $500/month for seed-stage startups."
)
MRR_CONTENT = "Current MRR is $25000"


def reset_demo(db: Session) -> ResetDemoResponse:
    relationships_deleted = db.scalar(select(func.count()).select_from(KnowledgeRelationship)) or 0
    items_deleted = db.scalar(select(func.count()).select_from(KnowledgeItem)) or 0

    db.execute(delete(KnowledgeRelationship))
    db.execute(delete(KnowledgeItem))
    db.flush()

    for payload in SEED_ITEMS:
        item_data = payload.model_dump()
        item_data["source_priority"] = get_source_priority(payload.source_system)
        db.add(KnowledgeItem(**item_data))

    db.flush()

    pricing_item = db.scalar(
        select(KnowledgeItem).where(KnowledgeItem.content == PRICING_DECISION_CONTENT)
    )
    mrr_item = db.scalar(
        select(KnowledgeItem).where(KnowledgeItem.content == MRR_CONTENT)
    )

    relationships_created = 0
    if pricing_item is not None and mrr_item is not None:
        db.add(
            KnowledgeRelationship(
                source_knowledge_id=pricing_item.id,
                target_knowledge_id=mrr_item.id,
                relationship_type="affects",
            )
        )
        relationships_created = 1

    db.commit()

    return ResetDemoResponse(
        relationships_deleted=relationships_deleted,
        items_deleted=items_deleted,
        items_created=len(SEED_ITEMS),
        relationships_created=relationships_created,
    )
