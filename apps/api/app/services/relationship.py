from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.models.knowledge_relationship import KnowledgeRelationship
from app.schemas.knowledge_relationship import KnowledgeRelationshipCreate

SEED_RELATIONSHIPS = [
    (
        "We decided to price Authority AI at $500/month for seed-stage startups.",
        "Current MRR is $25000",
        "affects",
    ),
]


def create_knowledge_relationship(
    db: Session, payload: KnowledgeRelationshipCreate
) -> KnowledgeRelationship:
    if payload.source_id == payload.target_id:
        raise HTTPException(
            status_code=400,
            detail="source_id and target_id must be different",
        )

    source = db.get(KnowledgeItem, payload.source_id)
    if source is None:
        raise HTTPException(
            status_code=404,
            detail=f"KnowledgeItem with id {payload.source_id} not found",
        )

    target = db.get(KnowledgeItem, payload.target_id)
    if target is None:
        raise HTTPException(
            status_code=404,
            detail=f"KnowledgeItem with id {payload.target_id} not found",
        )

    relationship = KnowledgeRelationship(
        source_knowledge_id=payload.source_id,
        target_knowledge_id=payload.target_id,
        relationship_type=payload.relationship_type,
    )
    db.add(relationship)
    db.commit()
    db.refresh(relationship)
    return relationship


def get_knowledge_relationships(
    db: Session, knowledge_id: int
) -> tuple[KnowledgeItem, list[KnowledgeRelationship]]:
    item = db.get(KnowledgeItem, knowledge_id)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail=f"KnowledgeItem with id {knowledge_id} not found",
        )

    relationships = list(
        db.scalars(
            select(KnowledgeRelationship)
            .where(
                or_(
                    KnowledgeRelationship.source_knowledge_id == knowledge_id,
                    KnowledgeRelationship.target_knowledge_id == knowledge_id,
                )
            )
            .order_by(KnowledgeRelationship.id)
        ).all()
    )

    return item, relationships


def seed_knowledge_relationships(db: Session) -> tuple[int, int]:
    count_created = 0
    count_skipped = 0

    for source_content, target_content, relationship_type in SEED_RELATIONSHIPS:
        source = db.scalar(
            select(KnowledgeItem).where(KnowledgeItem.content == source_content)
        )
        target = db.scalar(
            select(KnowledgeItem).where(KnowledgeItem.content == target_content)
        )

        if source is None or target is None:
            continue

        existing = db.scalar(
            select(KnowledgeRelationship).where(
                KnowledgeRelationship.source_knowledge_id == source.id,
                KnowledgeRelationship.target_knowledge_id == target.id,
                KnowledgeRelationship.relationship_type == relationship_type,
            )
        )
        if existing:
            count_skipped += 1
            continue

        db.add(
            KnowledgeRelationship(
                source_knowledge_id=source.id,
                target_knowledge_id=target.id,
                relationship_type=relationship_type,
            )
        )
        count_created += 1

    db.commit()
    return count_created, count_skipped
