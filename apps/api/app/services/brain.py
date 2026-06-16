from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_definition import KnowledgeDefinition
from app.models.knowledge_item import KnowledgeItem
from app.schemas.brain import (
    BrainCoverageResponse,
    BrainCoverageSlotRead,
    BrainSubDomainRead,
    KnowledgeDefinitionCreate,
)

BRAIN_DEFINITIONS = [
    KnowledgeDefinitionCreate(
        domain="financial",
        sub_domain="mrr",
        name="Monthly Recurring Revenue",
        description="Current monthly recurring revenue.",
        source_of_truth="stripe",
        allowed_roles=["founder", "finance"],
    ),
    KnowledgeDefinitionCreate(
        domain="financial",
        sub_domain="runway",
        name="Runway",
        description="Current cash runway in months.",
        source_of_truth="notion",
        allowed_roles=["founder", "finance"],
    ),
    KnowledgeDefinitionCreate(
        domain="pipeline",
        sub_domain="objection",
        name="Objections",
        description="Most common sales objections and how to handle them.",
        source_of_truth="hubspot",
        allowed_roles=["founder", "sales", "member"],
    ),
    KnowledgeDefinitionCreate(
        domain="mission",
        sub_domain="icp",
        name="Ideal Customer Profile",
        description="Target customer segment the company serves.",
        source_of_truth="notion",
        allowed_roles=["founder", "member"],
    ),
    KnowledgeDefinitionCreate(
        domain="mission",
        sub_domain="product",
        name="Product",
        description="What the company builds and why it exists.",
        source_of_truth="notion",
        allowed_roles=["founder", "member"],
    ),
    KnowledgeDefinitionCreate(
        domain="engineering",
        sub_domain="blocker",
        name="Blockers",
        description="Current engineering blockers and delivery risks.",
        source_of_truth="linear",
        allowed_roles=["founder", "engineering"],
    ),
    KnowledgeDefinitionCreate(
        domain="decisions",
        sub_domain="pricing",
        name="Pricing",
        description="Pricing decisions, plans, and rationale.",
        source_of_truth="notion",
        allowed_roles=["founder", "sales"],
    ),
]


def seed_brain_definitions(db: Session) -> tuple[int, int]:
    count_created = 0
    count_skipped = 0

    for payload in BRAIN_DEFINITIONS:
        existing = db.scalar(
            select(KnowledgeDefinition).where(
                KnowledgeDefinition.domain == payload.domain,
                KnowledgeDefinition.sub_domain == payload.sub_domain,
            )
        )
        if existing:
            count_skipped += 1
            continue

        db.add(KnowledgeDefinition(**payload.model_dump()))
        count_created += 1

    if count_created:
        db.commit()

    return count_created, count_skipped


def initialize_brain() -> tuple[int, int]:
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        return seed_brain_definitions(db)


def get_brain_structure(db: Session) -> dict[str, list[BrainSubDomainRead]]:
    definitions = db.scalars(
        select(KnowledgeDefinition).order_by(
            KnowledgeDefinition.domain,
            KnowledgeDefinition.sub_domain,
        )
    ).all()

    brain: dict[str, list[BrainSubDomainRead]] = {}
    for definition in definitions:
        brain.setdefault(definition.domain, []).append(
            BrainSubDomainRead(
                sub_domain=definition.sub_domain,
                source_of_truth=definition.source_of_truth,
            )
        )

    return brain


def get_brain_coverage(db: Session) -> BrainCoverageResponse:
    definitions = db.scalars(
        select(KnowledgeDefinition).order_by(
            KnowledgeDefinition.domain,
            KnowledgeDefinition.sub_domain,
        )
    ).all()

    populated_slots = {
        (domain, sub_domain)
        for domain, sub_domain in db.execute(
            select(KnowledgeItem.domain, KnowledgeItem.sub_domain).distinct()
        ).all()
    }

    domains: dict[str, list[BrainCoverageSlotRead]] = {}
    populated_count = 0

    for definition in definitions:
        is_populated = (definition.domain, definition.sub_domain) in populated_slots
        if is_populated:
            populated_count += 1

        domains.setdefault(definition.domain, []).append(
            BrainCoverageSlotRead(
                sub_domain=definition.sub_domain,
                name=definition.name,
                status="populated" if is_populated else "missing",
            )
        )

    total = len(definitions)
    coverage_percent = round(populated_count / total * 100) if total else 0

    return BrainCoverageResponse(
        coverage_percent=coverage_percent,
        domains=domains,
    )
