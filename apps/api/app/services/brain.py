from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_definition import KnowledgeDefinition
from app.models.knowledge_item import KnowledgeItem
from app.schemas.brain import (
    BrainConflictRead,
    BrainConflictsResponse,
    BrainCoverageResponse,
    BrainCoverageSlotRead,
    BrainFreshnessResponse,
    BrainFreshnessSlotRead,
    BrainHealthPriorityRead,
    BrainHealthResponse,
    BrainLineageItemRead,
    BrainLineageResponse,
    BrainRecommendationRead,
    BrainRecommendationsResponse,
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
        importance_score=10,
    ),
    KnowledgeDefinitionCreate(
        domain="financial",
        sub_domain="runway",
        name="Runway",
        description="Current cash runway in months.",
        source_of_truth="notion",
        allowed_roles=["founder", "finance"],
        importance_score=10,
    ),
    KnowledgeDefinitionCreate(
        domain="pipeline",
        sub_domain="objection",
        name="Objections",
        description="Most common sales objections and how to handle them.",
        source_of_truth="hubspot",
        allowed_roles=["founder", "sales", "member"],
        importance_score=9,
    ),
    KnowledgeDefinitionCreate(
        domain="mission",
        sub_domain="icp",
        name="Ideal Customer Profile",
        description="Target customer segment the company serves.",
        source_of_truth="notion",
        allowed_roles=["founder", "member"],
        importance_score=6,
    ),
    KnowledgeDefinitionCreate(
        domain="mission",
        sub_domain="product",
        name="Product",
        description="What the company builds and why it exists.",
        source_of_truth="notion",
        allowed_roles=["founder", "member"],
        importance_score=5,
    ),
    KnowledgeDefinitionCreate(
        domain="engineering",
        sub_domain="blocker",
        name="Blockers",
        description="Current engineering blockers and delivery risks.",
        source_of_truth="linear",
        allowed_roles=["founder", "engineering"],
        importance_score=8,
    ),
    KnowledgeDefinitionCreate(
        domain="decisions",
        sub_domain="pricing",
        name="Pricing",
        description="Pricing decisions, plans, and rationale.",
        source_of_truth="notion",
        allowed_roles=["founder", "sales"],
        importance_score=8,
    ),
]


RECOMMENDATION_REASON = "Knowledge definition exists but no knowledge item found."

DOMAIN_PRIORITY: dict[str, Literal["high", "medium", "low"]] = {
    "financial": "high",
    "pipeline": "high",
    "decisions": "medium",
    "engineering": "medium",
    "mission": "low",
}

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

DOMAIN_FRESHNESS_DAYS: dict[str, int] = {
    "financial": 7,
    "pipeline": 14,
    "engineering": 7,
    "decisions": 30,
    "mission": 90,
}


def _pick_highest_priority_item(
    items: list[KnowledgeItem],
) -> KnowledgeItem | None:
    if not items:
        return None

    return min(items, key=lambda item: (item.source_priority, item.trust_rank))


def _freshness_status(
    item: KnowledgeItem | None, domain: str, now: datetime
) -> Literal["fresh", "stale", "missing"]:
    if item is None:
        return "missing"

    window_days = DOMAIN_FRESHNESS_DAYS.get(domain, 30)
    updated_at = item.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    age = now - updated_at
    if age <= timedelta(days=window_days):
        return "fresh"

    return "stale"


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


def sync_definition_importance_scores() -> int:
    from app.db.session import SessionLocal

    updated = 0
    with SessionLocal() as db:
        for payload in BRAIN_DEFINITIONS:
            existing = db.scalar(
                select(KnowledgeDefinition).where(
                    KnowledgeDefinition.domain == payload.domain,
                    KnowledgeDefinition.sub_domain == payload.sub_domain,
                )
            )
            if existing is None:
                continue

            if existing.importance_score != payload.importance_score:
                existing.importance_score = payload.importance_score
                updated += 1

        if updated:
            db.commit()

    return updated


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


def get_brain_recommendations(db: Session) -> BrainRecommendationsResponse:
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

    recommendations: list[BrainRecommendationRead] = []
    for definition in definitions:
        if (definition.domain, definition.sub_domain) in populated_slots:
            continue

        priority = DOMAIN_PRIORITY.get(definition.domain, "low")
        recommendations.append(
            BrainRecommendationRead(
                domain=definition.domain,
                sub_domain=definition.sub_domain,
                name=definition.name,
                source_of_truth=definition.source_of_truth,
                reason=RECOMMENDATION_REASON,
                priority=priority,
            )
        )

    recommendations.sort(
        key=lambda recommendation: (
            PRIORITY_ORDER[recommendation.priority],
            recommendation.domain,
            recommendation.sub_domain,
        )
    )

    return BrainRecommendationsResponse(recommendations=recommendations)


def get_brain_freshness(db: Session) -> BrainFreshnessResponse:
    definitions = db.scalars(
        select(KnowledgeDefinition).order_by(
            KnowledgeDefinition.domain,
            KnowledgeDefinition.sub_domain,
        )
    ).all()

    all_items = db.scalars(select(KnowledgeItem)).all()
    items_by_slot: dict[tuple[str, str], list[KnowledgeItem]] = {}
    for item in all_items:
        items_by_slot.setdefault((item.domain, item.sub_domain), []).append(item)

    now = datetime.now(timezone.utc)
    domains: dict[str, list[BrainFreshnessSlotRead]] = {}
    fresh_count = 0

    for definition in definitions:
        slot_items = items_by_slot.get(
            (definition.domain, definition.sub_domain),
            [],
        )
        best_item = _pick_highest_priority_item(slot_items)
        status = _freshness_status(best_item, definition.domain, now)

        if status == "fresh":
            fresh_count += 1

        domains.setdefault(definition.domain, []).append(
            BrainFreshnessSlotRead(
                sub_domain=definition.sub_domain,
                name=definition.name,
                status=status,
            )
        )

    total = len(definitions)
    brain_health_percent = round(fresh_count / total * 100) if total else 0

    return BrainFreshnessResponse(
        brain_health_percent=brain_health_percent,
        domains=domains,
    )


def _weighted_score(earned: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round(earned / total, 4)


def get_brain_health(db: Session) -> BrainHealthResponse:
    definitions = db.scalars(
        select(KnowledgeDefinition).order_by(
            KnowledgeDefinition.domain,
            KnowledgeDefinition.sub_domain,
        )
    ).all()

    all_items = db.scalars(select(KnowledgeItem)).all()
    items_by_slot: dict[tuple[str, str], list[KnowledgeItem]] = {}
    for item in all_items:
        items_by_slot.setdefault((item.domain, item.sub_domain), []).append(item)

    now = datetime.now(timezone.utc)
    total_importance = sum(definition.importance_score for definition in definitions)
    populated_importance = 0
    fresh_importance = 0
    high_priority_missing: list[BrainHealthPriorityRead] = []
    high_priority_stale: list[BrainHealthPriorityRead] = []

    for definition in definitions:
        slot_items = items_by_slot.get(
            (definition.domain, definition.sub_domain),
            [],
        )
        best_item = _pick_highest_priority_item(slot_items)
        status = _freshness_status(best_item, definition.domain, now)
        priority_entry = BrainHealthPriorityRead(
            domain=definition.domain,
            sub_domain=definition.sub_domain,
            name=definition.name,
            importance_score=definition.importance_score,
        )

        if status == "missing":
            high_priority_missing.append(priority_entry)
            continue

        populated_importance += definition.importance_score
        if status == "fresh":
            fresh_importance += definition.importance_score
        else:
            high_priority_stale.append(priority_entry)

    high_priority_missing.sort(key=lambda entry: entry.importance_score, reverse=True)
    high_priority_stale.sort(key=lambda entry: entry.importance_score, reverse=True)

    return BrainHealthResponse(
        weighted_coverage_score=_weighted_score(
            populated_importance, total_importance
        ),
        weighted_freshness_score=_weighted_score(fresh_importance, total_importance),
        brain_health_score=_weighted_score(fresh_importance, total_importance),
        high_priority_missing=high_priority_missing,
        high_priority_stale=high_priority_stale,
    )


def get_brain_conflicts(db: Session) -> BrainConflictsResponse:
    definitions = db.scalars(
        select(KnowledgeDefinition).order_by(
            KnowledgeDefinition.domain,
            KnowledgeDefinition.sub_domain,
        )
    ).all()

    all_items = db.scalars(select(KnowledgeItem)).all()
    items_by_slot: dict[tuple[str, str], list[KnowledgeItem]] = {}
    for item in all_items:
        items_by_slot.setdefault((item.domain, item.sub_domain), []).append(item)

    conflicts: list[BrainConflictRead] = []

    for definition in definitions:
        slot_items = items_by_slot.get(
            (definition.domain, definition.sub_domain),
            [],
        )
        if len(slot_items) < 2:
            continue

        distinct_values = {item.content for item in slot_items}
        if len(distinct_values) < 2:
            continue

        winning_item = _pick_highest_priority_item(slot_items)
        if winning_item is None:
            continue

        conflicts.append(
            BrainConflictRead(
                domain=definition.domain,
                sub_domain=definition.sub_domain,
                conflicting_sources=[
                    item.source_system
                    for item in sorted(
                        slot_items,
                        key=lambda item: (item.source_priority, item.trust_rank),
                    )
                ],
                conflicting_values=sorted(distinct_values),
                winning_source=winning_item.source_system,
            )
        )

    total_definitions = len(definitions)
    conflict_count = len(conflicts)
    consistency_score = (
        round(1 - conflict_count / total_definitions, 4)
        if total_definitions
        else 1.0
    )

    return BrainConflictsResponse(
        conflict_count=conflict_count,
        consistency_score=consistency_score,
        conflicts=conflicts,
    )


def get_brain_lineage(db: Session) -> BrainLineageResponse:
    items = db.scalars(
        select(KnowledgeItem).order_by(
            KnowledgeItem.domain,
            KnowledgeItem.sub_domain,
            KnowledgeItem.source_priority,
            KnowledgeItem.trust_rank,
        )
    ).all()

    domains: dict[str, list[BrainLineageItemRead]] = {}
    for item in items:
        domains.setdefault(item.domain, []).append(
            BrainLineageItemRead(
                domain=item.domain,
                sub_domain=item.sub_domain,
                content=item.content,
                source_system=item.source_system,
                source_url=item.source_url,
                created_at=item.created_at,
                updated_at=item.updated_at,
                trust_rank=item.trust_rank,
                source_priority=item.source_priority,
            )
        )

    for domain_items in domains.values():
        domain_items.sort(key=lambda entry: (entry.source_priority, entry.trust_rank))

    return BrainLineageResponse(domains=domains)
