from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.models.knowledge_relationship import KnowledgeRelationship
from app.schemas.seed import CleanDemoResponse, ConflictTestResponse, ResetDemoResponse
from app.services.knowledge import SEED_ITEMS
from app.services.source_priority import get_source_priority

PRICING_DECISION_CONTENT = (
    "We decided to price Authority AI at $500/month for seed-stage startups."
)
MRR_CONTENT = "Current MRR is $25000"

FRESHNESS_TEST_ITEMS = [
    {
        "domain": "financial",
        "sub_domain": "mrr",
        "content": "Current MRR is $25000",
        "source_system": "stripe",
        "source_priority": 1,
        "trust_rank": 1,
        "updated_at_offset_days": 0,
        "allowed_roles": ["founder", "finance"],
    },
    {
        "domain": "financial",
        "sub_domain": "runway",
        "content": "Current runway is 14 months",
        "source_system": "notion",
        "source_priority": 5,
        "trust_rank": 4,
        "updated_at_offset_days": 20,
        "allowed_roles": ["founder", "finance"],
    },
    {
        "domain": "pipeline",
        "sub_domain": "objection",
        "content": "Most common objection is security concerns around integrations",
        "source_system": "hubspot",
        "source_priority": 3,
        "trust_rank": 3,
        "updated_at_offset_days": 0,
        "allowed_roles": ["founder", "sales", "member"],
    },
    {
        "domain": "engineering",
        "sub_domain": "blocker",
        "content": "Current blocker is Slack OAuth implementation",
        "source_system": "linear",
        "source_priority": 4,
        "trust_rank": 3,
        "updated_at_offset_days": 10,
        "allowed_roles": ["founder", "engineering"],
    },
    {
        "domain": "mission",
        "sub_domain": "icp",
        "content": "Ideal customer profile is YC-backed B2B SaaS startups with 5-50 employees",
        "source_system": "notion",
        "source_priority": 5,
        "trust_rank": 4,
        "updated_at_offset_days": 45,
        "allowed_roles": ["founder", "member"],
    },
]

CONFLICT_TEST_ITEMS = [
    {
        "domain": "financial",
        "sub_domain": "mrr",
        "content": "Current MRR is $25000",
        "source_system": "stripe",
        "source_url": "https://stripe.com/example",
        "source_priority": 1,
        "trust_rank": 1,
        "allowed_roles": ["founder", "finance"],
    },
    {
        "domain": "financial",
        "sub_domain": "mrr",
        "content": "Current MRR is $30000",
        "source_system": "notion",
        "source_url": "https://notion.so/mrr",
        "source_priority": 5,
        "trust_rank": 4,
        "allowed_roles": ["founder", "finance"],
    },
]

NOTION_CONFLICT_MRR_CONTENT = "Current MRR is $30000"
STRIPE_MRR_SPEC = CONFLICT_TEST_ITEMS[0]
NOTION_MRR_SPEC = CONFLICT_TEST_ITEMS[1]

CLEAN_DEMO_ITEMS = [
    {
        "domain": "financial",
        "sub_domain": "mrr",
        "content": "Current MRR is $25000",
        "source_system": "stripe",
        "source_url": "https://stripe.com/example",
        "source_priority": 1,
        "trust_rank": 1,
        "allowed_roles": ["founder", "finance"],
    },
    {
        "domain": "financial",
        "sub_domain": "runway",
        "content": "Current runway is 14 months",
        "source_system": "notion",
        "source_url": "https://notion.so/runway",
        "source_priority": 5,
        "trust_rank": 4,
        "allowed_roles": ["founder", "finance"],
    },
    {
        "domain": "decisions",
        "sub_domain": "pricing",
        "content": "We decided to price Authority AI at $500/month for seed-stage startups.",
        "source_system": "notion",
        "source_url": "https://notion.so/pricing",
        "source_priority": 5,
        "trust_rank": 4,
        "allowed_roles": ["founder", "sales"],
    },
    {
        "domain": "pipeline",
        "sub_domain": "objection",
        "content": "Most common objection is security concerns around integrations.",
        "source_system": "hubspot",
        "source_url": "https://hubspot.com/example",
        "source_priority": 3,
        "trust_rank": 3,
        "allowed_roles": ["founder", "sales"],
    },
    {
        "domain": "engineering",
        "sub_domain": "blocker",
        "content": "Current blocker is Slack OAuth implementation.",
        "source_system": "linear",
        "source_url": "https://linear.app/example",
        "source_priority": 4,
        "trust_rank": 3,
        "allowed_roles": ["founder", "engineering"],
    },
    {
        "domain": "mission",
        "sub_domain": "icp",
        "content": "Ideal customer profile is YC-backed B2B SaaS startups with 5-50 employees.",
        "source_system": "notion",
        "source_url": "https://notion.so/icp",
        "source_priority": 5,
        "trust_rank": 4,
        "allowed_roles": ["founder", "sales", "engineering"],
    },
    {
        "domain": "mission",
        "sub_domain": "product",
        "content": "Authority AI is a schema-first company brain for startup teams.",
        "source_system": "notion",
        "source_url": "https://notion.so/product",
        "source_priority": 5,
        "trust_rank": 4,
        "allowed_roles": ["founder", "sales", "engineering"],
    },
]

CLEAN_DEMO_RELATIONSHIPS = [
    (
        "We decided to price Authority AI at $500/month for seed-stage startups.",
        "Current MRR is $25000",
        "affects",
    ),
    (
        "Most common objection is security concerns around integrations.",
        "Current blocker is Slack OAuth implementation.",
        "related_to",
    ),
    (
        "Ideal customer profile is YC-backed B2B SaaS startups with 5-50 employees.",
        "Authority AI is a schema-first company brain for startup teams.",
        "informs",
    ),
]


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


def seed_freshness_test(db: Session) -> list[KnowledgeItem]:
    db.execute(delete(KnowledgeRelationship))
    db.execute(delete(KnowledgeItem))
    db.flush()

    now = datetime.now(timezone.utc)
    items: list[KnowledgeItem] = []

    for spec in FRESHNESS_TEST_ITEMS:
        updated_at = now - timedelta(days=spec["updated_at_offset_days"])
        item = KnowledgeItem(
            domain=spec["domain"],
            sub_domain=spec["sub_domain"],
            content=spec["content"],
            source_system=spec["source_system"],
            source_url="",
            source_priority=spec["source_priority"],
            trust_rank=spec["trust_rank"],
            allowed_roles=spec["allowed_roles"],
            created_at=updated_at,
            updated_at=updated_at,
        )
        db.add(item)
        items.append(item)

    db.commit()
    for item in items:
        db.refresh(item)

    return items


def _apply_mrr_spec(item: KnowledgeItem, spec: dict, now: datetime) -> None:
    item.content = spec["content"]
    item.source_url = spec["source_url"]
    item.source_priority = spec["source_priority"]
    item.trust_rank = spec["trust_rank"]
    item.allowed_roles = spec["allowed_roles"]
    item.updated_at = now


def _create_mrr_item(spec: dict, now: datetime) -> KnowledgeItem:
    return KnowledgeItem(
        domain=spec["domain"],
        sub_domain=spec["sub_domain"],
        content=spec["content"],
        source_system=spec["source_system"],
        source_url=spec["source_url"],
        source_priority=spec["source_priority"],
        trust_rank=spec["trust_rank"],
        allowed_roles=spec["allowed_roles"],
        created_at=now,
        updated_at=now,
    )


def seed_conflict_test(db: Session) -> ConflictTestResponse:
    now = datetime.now(timezone.utc)
    created_or_updated: list[KnowledgeItem] = []

    notion_conflict_items = list(
        db.scalars(
            select(KnowledgeItem).where(
                KnowledgeItem.domain == "financial",
                KnowledgeItem.sub_domain == "mrr",
                KnowledgeItem.source_system == "notion",
                KnowledgeItem.content == NOTION_CONFLICT_MRR_CONTENT,
            )
        ).all()
    )
    for duplicate in notion_conflict_items[1:]:
        db.delete(duplicate)
    if len(notion_conflict_items) > 1:
        db.flush()

    stripe_item = db.scalar(
        select(KnowledgeItem).where(
            KnowledgeItem.domain == "financial",
            KnowledgeItem.sub_domain == "mrr",
            KnowledgeItem.source_system == "stripe",
        )
    )
    if stripe_item is None:
        stripe_item = _create_mrr_item(STRIPE_MRR_SPEC, now)
        db.add(stripe_item)
    else:
        _apply_mrr_spec(stripe_item, STRIPE_MRR_SPEC, now)
    created_or_updated.append(stripe_item)

    notion_item = (
        notion_conflict_items[0]
        if notion_conflict_items
        else db.scalar(
            select(KnowledgeItem).where(
                KnowledgeItem.domain == "financial",
                KnowledgeItem.sub_domain == "mrr",
                KnowledgeItem.source_system == "notion",
            )
        )
    )
    if notion_item is None:
        notion_item = _create_mrr_item(NOTION_MRR_SPEC, now)
        db.add(notion_item)
    else:
        _apply_mrr_spec(notion_item, NOTION_MRR_SPEC, now)
    created_or_updated.append(notion_item)

    db.commit()
    for item in created_or_updated:
        db.refresh(item)

    return ConflictTestResponse(created_or_updated=created_or_updated)


def seed_clean_demo(db: Session) -> CleanDemoResponse:
    deleted_relationships = (
        db.scalar(select(func.count()).select_from(KnowledgeRelationship)) or 0
    )
    deleted_knowledge_items = (
        db.scalar(select(func.count()).select_from(KnowledgeItem)) or 0
    )

    db.execute(delete(KnowledgeRelationship))
    db.execute(delete(KnowledgeItem))
    db.flush()

    now = datetime.now(timezone.utc)
    for spec in CLEAN_DEMO_ITEMS:
        db.add(
            KnowledgeItem(
                domain=spec["domain"],
                sub_domain=spec["sub_domain"],
                content=spec["content"],
                source_system=spec["source_system"],
                source_url=spec["source_url"],
                source_priority=spec["source_priority"],
                trust_rank=spec["trust_rank"],
                allowed_roles=spec["allowed_roles"],
                created_at=now,
                updated_at=now,
            )
        )

    db.flush()

    created_relationships = 0
    for source_content, target_content, relationship_type in CLEAN_DEMO_RELATIONSHIPS:
        source = db.scalar(
            select(KnowledgeItem).where(KnowledgeItem.content == source_content)
        )
        target = db.scalar(
            select(KnowledgeItem).where(KnowledgeItem.content == target_content)
        )
        if source is None or target is None:
            continue

        db.add(
            KnowledgeRelationship(
                source_knowledge_id=source.id,
                target_knowledge_id=target.id,
                relationship_type=relationship_type,
            )
        )
        created_relationships += 1

    db.commit()

    return CleanDemoResponse(
        deleted_knowledge_items=deleted_knowledge_items,
        deleted_relationships=deleted_relationships,
        created_knowledge_items=len(CLEAN_DEMO_ITEMS),
        created_relationships=created_relationships,
    )
