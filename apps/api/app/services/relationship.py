from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.knowledge_definition import KnowledgeDefinition
from app.models.knowledge_item import KnowledgeItem
from app.models.knowledge_relationship import KnowledgeRelationship
from app.schemas.knowledge_relationship import (
    BrainRelationshipRead,
    BrainRelationshipsResponse,
    KnowledgeImpactRead,
    KnowledgeImpactResponse,
    KnowledgeNodeRead,
    KnowledgeRelationshipCreate,
)
from app.services.brain import _pick_highest_priority_item

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


def _definition_names(db: Session) -> dict[tuple[str, str], str]:
    definitions = db.scalars(select(KnowledgeDefinition)).all()
    return {
        (definition.domain, definition.sub_domain): definition.name
        for definition in definitions
    }


def _node_from_item(
    item: KnowledgeItem, definition_names: dict[tuple[str, str], str]
) -> KnowledgeNodeRead:
    return KnowledgeNodeRead(
        domain=item.domain,
        sub_domain=item.sub_domain,
        name=definition_names.get(
            (item.domain, item.sub_domain),
            item.sub_domain,
        ),
    )


def get_knowledge_impact(
    db: Session, domain: str, sub_domain: str
) -> KnowledgeImpactResponse:
    definition_names = _definition_names(db)
    source_item = _pick_highest_priority_item(
        list(
            db.scalars(
                select(KnowledgeItem).where(
                    KnowledgeItem.domain == domain,
                    KnowledgeItem.sub_domain == sub_domain,
                )
            ).all()
        )
    )

    if source_item is None:
        return KnowledgeImpactResponse(impacts=[])

    source_node = _node_from_item(source_item, definition_names)
    relationships = db.scalars(
        select(KnowledgeRelationship).where(
            KnowledgeRelationship.source_knowledge_id == source_item.id
        )
    ).all()

    items_by_id = {
        item.id: item
        for item in db.scalars(select(KnowledgeItem)).all()
    }

    impacts: list[KnowledgeImpactRead] = []
    for relationship in relationships:
        target_item = items_by_id.get(relationship.target_knowledge_id)
        if target_item is None:
            continue

        impacts.append(
            KnowledgeImpactRead(
                source=source_node,
                target=_node_from_item(target_item, definition_names),
                relationship_type=relationship.relationship_type,
            )
        )

    return KnowledgeImpactResponse(impacts=impacts)


def get_brain_relationships(db: Session) -> BrainRelationshipsResponse:
    definition_names = _definition_names(db)
    items_by_id = {
        item.id: item for item in db.scalars(select(KnowledgeItem)).all()
    }

    domains: dict[str, list[BrainRelationshipRead]] = {}
    relationships = db.scalars(select(KnowledgeRelationship)).all()

    for relationship in relationships:
        source_item = items_by_id.get(relationship.source_knowledge_id)
        target_item = items_by_id.get(relationship.target_knowledge_id)
        if source_item is None or target_item is None:
            continue

        domains.setdefault(source_item.domain, []).append(
            BrainRelationshipRead(
                source=_node_from_item(source_item, definition_names),
                target=_node_from_item(target_item, definition_names),
                relationship_type=relationship.relationship_type,
            )
        )

    return BrainRelationshipsResponse(domains=domains)
