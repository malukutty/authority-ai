from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.models.knowledge_relationship import KnowledgeRelationship
from app.schemas.decision import (
    AffectedObjectRead,
    AuthorityUsedRead,
    ChangedObjectRead,
    DecisionChangeInput,
    DecisionReadinessRead,
    DecisionSimulationResponse,
    LowAuthorityObjectRead,
)
from app.services.brain import _pick_highest_priority_item

SOURCE_SYSTEM_AUTHORITY_SCORES: dict[str, int] = {
    "stripe": 100,
    "founder_input": 95,
    "public_website": 80,
    "website_import": 75,
    "notion": 85,
    "hubspot": 85,
    "linear": 85,
    "manual_seed": 60,
}

DEFAULT_AUTHORITY_SCORE = 50
LOW_AUTHORITY_THRESHOLD = 60
READY_AVERAGE_THRESHOLD = 80
REVIEW_AVERAGE_THRESHOLD = 60

DECISION_LABELS: dict[tuple[str, str], str] = {
    ("decisions", "pricing"): "Pricing Change",
    ("mission", "icp"): "ICP Change",
    ("engineering", "blocker"): "Engineering Blocker Change",
    ("financial", "runway"): "Runway Change",
    ("financial", "mrr"): "MRR Change",
}

FALLBACK_RELATIONSHIPS: dict[tuple[str, str], list[tuple[str, str, str]]] = {
    ("decisions", "pricing"): [
        ("financial", "mrr", "affects"),
        ("pipeline", "objection", "affects"),
        ("mission", "icp", "affects"),
        ("source", "public_pricing_page", "affects"),
    ],
    ("mission", "icp"): [
        ("pipeline", "objection", "affects"),
        ("sales", "motion", "affects"),
        ("financial", "mrr", "affects"),
    ],
    ("engineering", "blocker"): [
        ("product", "category", "affects"),
        ("team", "culture", "affects"),
    ],
    ("pipeline", "objection"): [
        ("decisions", "pricing", "affects"),
        ("mission", "product", "affects"),
    ],
    ("financial", "runway"): [
        ("company", "stage", "affects"),
        ("team", "culture", "affects"),
    ],
    ("financial", "mrr"): [
        ("financial", "runway", "affects"),
        ("decisions", "pricing", "affects"),
    ],
}

RECOMMENDED_CHECKS: dict[tuple[str, str], list[str]] = {
    ("decisions", "pricing"): [
        "Review impact on monthly recurring revenue.",
        "Review current customer objections before changing pricing.",
        "Update pricing documentation.",
        "Confirm ICP still matches the new pricing.",
        "Prepare customer communication.",
    ],
    ("mission", "icp"): [
        "Review sales objections.",
        "Review product positioning.",
        "Check whether pricing still matches the target customer.",
        "Review affected pipeline segments.",
    ],
    ("engineering", "blocker"): [
        "Review affected product roadmap.",
        "Review team capacity.",
        "Check whether customer-facing commitments are impacted.",
    ],
    ("financial", "runway"): [
        "Review hiring plans.",
        "Review fundraising timeline.",
        "Review monthly burn assumptions.",
    ],
    ("financial", "mrr"): [
        "Review runway impact.",
        "Review pricing assumptions.",
        "Review pipeline quality.",
    ],
}

DEFAULT_RECOMMENDED_CHECKS = [
    "Review affected knowledge objects.",
    "Confirm source-of-truth owners.",
    "Check whether downstream decisions rely on this knowledge.",
]

INCOMPLETE_MARKERS = (
    "tbd",
    "placeholder",
    "not available",
    "pricing page available",
    "go-to-market aligned to unknown",
    "unknown employees",
)


def is_incomplete_knowledge(content: str) -> bool:
    if not content.strip():
        return True

    normalized = content.strip()
    if normalized.lower() == "unknown":
        return True

    lowered = normalized.lower()
    if "unknown" in lowered:
        return True

    return any(marker in lowered for marker in INCOMPLETE_MARKERS)


def infer_authority_score(item: KnowledgeItem) -> int:
    metadata = getattr(item, "metadata", None)
    if isinstance(metadata, dict) and metadata.get("authority_score") is not None:
        return int(metadata["authority_score"])

    return SOURCE_SYSTEM_AUTHORITY_SCORES.get(
        item.source_system.lower(),
        DEFAULT_AUTHORITY_SCORE,
    )


def _decision_label(domain: str, sub_domain: str) -> str:
    return DECISION_LABELS.get(
        (domain, sub_domain),
        f"{sub_domain.replace('_', ' ').title()} Change",
    )


def _active_items_for_slot(
    db: Session,
    domain: str,
    sub_domain: str,
) -> list[KnowledgeItem]:
    return list(
        db.scalars(
            select(KnowledgeItem).where(
                KnowledgeItem.domain == domain,
                KnowledgeItem.sub_domain == sub_domain,
                KnowledgeItem.is_active.is_(True),
            )
        ).all()
    )


def find_changed_object(
    db: Session,
    domain: str,
    sub_domain: str,
    new_value: str,
) -> ChangedObjectRead | None:
    item = _pick_highest_priority_item(_active_items_for_slot(db, domain, sub_domain))
    if item is None:
        return None

    return ChangedObjectRead(
        domain=domain,
        sub_domain=sub_domain,
        current_value=item.content,
        new_value=new_value,
        authority_score=infer_authority_score(item),
    )


def _relationship_targets_from_db(
    db: Session,
    source_item: KnowledgeItem,
) -> list[tuple[str, str, str]]:
    items_by_id = {
        item.id: item for item in db.scalars(select(KnowledgeItem)).all()
    }
    relationships = db.scalars(
        select(KnowledgeRelationship).where(
            KnowledgeRelationship.source_knowledge_id == source_item.id
        )
    ).all()

    targets: list[tuple[str, str, str]] = []
    for relationship in relationships:
        target_item = items_by_id.get(relationship.target_knowledge_id)
        if target_item is None or not target_item.is_active:
            continue

        targets.append(
            (
                target_item.domain,
                target_item.sub_domain,
                relationship.relationship_type,
            )
        )

    return targets


def find_affected_objects(
    db: Session,
    domain: str,
    sub_domain: str,
) -> list[AffectedObjectRead]:
    source_item = _pick_highest_priority_item(
        _active_items_for_slot(db, domain, sub_domain)
    )
    if source_item is None:
        return []

    db_targets = _relationship_targets_from_db(db, source_item)
    if db_targets:
        relationship_targets = db_targets
    else:
        relationship_targets = FALLBACK_RELATIONSHIPS.get((domain, sub_domain), [])

    affected: list[AffectedObjectRead] = []
    seen_slots: set[tuple[str, str]] = set()

    for target_domain, target_sub_domain, relationship_type in relationship_targets:
        slot = (target_domain, target_sub_domain)
        if slot in seen_slots:
            continue
        seen_slots.add(slot)

        target_item = _pick_highest_priority_item(
            _active_items_for_slot(db, target_domain, target_sub_domain)
        )
        if target_item is None:
            continue

        affected.append(
            AffectedObjectRead(
                domain=target_domain,
                sub_domain=target_sub_domain,
                relationship=relationship_type,
                current_value=target_item.content,
                authority_score=infer_authority_score(target_item),
                source_system=target_item.source_system,
            )
        )

    return affected


def build_recommended_checks(
    change: DecisionChangeInput,
    affected_objects: list[AffectedObjectRead],
) -> list[str]:
    checks = list(
        RECOMMENDED_CHECKS.get((change.domain, change.sub_domain), DEFAULT_RECOMMENDED_CHECKS)
    )

    if not affected_objects:
        return checks

    return checks


def calculate_decision_readiness(
    changed_object: ChangedObjectRead | None,
    affected_objects: list[AffectedObjectRead],
) -> DecisionReadinessRead:
    if changed_object is None:
        return DecisionReadinessRead(
            status="insufficient_knowledge",
            reason="Authority AI does not have the knowledge object being changed.",
            average_authority_score=0,
            low_authority_objects=[],
        )

    if not affected_objects:
        return DecisionReadinessRead(
            status="needs_review",
            reason="No downstream relationships are available for this decision.",
            average_authority_score=float(changed_object.authority_score),
            low_authority_objects=_collect_low_authority_objects(
                changed_object,
                affected_objects,
            ),
        )

    scores = [changed_object.authority_score] + [
        obj.authority_score for obj in affected_objects
    ]
    average_score = round(sum(scores) / len(scores), 1)
    low_authority_objects = _collect_low_authority_objects(
        changed_object,
        affected_objects,
    )
    has_incomplete_knowledge = _has_incomplete_knowledge(
        changed_object,
        affected_objects,
    )

    if has_incomplete_knowledge:
        return DecisionReadinessRead(
            status="needs_review",
            reason="Some relevant knowledge is incomplete or placeholder knowledge.",
            average_authority_score=average_score,
            low_authority_objects=low_authority_objects,
        )

    if average_score >= READY_AVERAGE_THRESHOLD and not low_authority_objects:
        return DecisionReadinessRead(
            status="ready",
            reason="Relevant knowledge is available and sufficiently authoritative.",
            average_authority_score=average_score,
            low_authority_objects=[],
        )

    if average_score >= REVIEW_AVERAGE_THRESHOLD:
        return DecisionReadinessRead(
            status="needs_review",
            reason="Some relevant knowledge exists, but one or more objects should be reviewed.",
            average_authority_score=average_score,
            low_authority_objects=low_authority_objects,
        )

    return DecisionReadinessRead(
        status="insufficient_knowledge",
        reason="Authority AI does not have enough high-authority knowledge to support this decision.",
        average_authority_score=average_score,
        low_authority_objects=low_authority_objects,
    )


def _has_incomplete_knowledge(
    changed_object: ChangedObjectRead,
    affected_objects: list[AffectedObjectRead],
) -> bool:
    if is_incomplete_knowledge(changed_object.current_value):
        return True

    return any(
        is_incomplete_knowledge(obj.current_value) for obj in affected_objects
    )


def _collect_low_authority_objects(
    changed_object: ChangedObjectRead,
    affected_objects: list[AffectedObjectRead],
) -> list[LowAuthorityObjectRead]:
    candidates = [
        (
            changed_object.domain,
            changed_object.sub_domain,
            changed_object.current_value,
            changed_object.authority_score,
        ),
        *[
            (obj.domain, obj.sub_domain, obj.current_value, obj.authority_score)
            for obj in affected_objects
        ],
    ]

    low_objects: list[LowAuthorityObjectRead] = []
    seen_slots: set[tuple[str, str]] = set()

    for domain, sub_domain, current_value, authority_score in candidates:
        slot = (domain, sub_domain)
        if slot in seen_slots:
            continue

        if is_incomplete_knowledge(current_value):
            low_objects.append(
                LowAuthorityObjectRead(
                    domain=domain,
                    sub_domain=sub_domain,
                    current_value=current_value,
                    authority_score=authority_score,
                    reason="Incomplete or placeholder knowledge",
                )
            )
            seen_slots.add(slot)
            continue

        if authority_score < LOW_AUTHORITY_THRESHOLD:
            low_objects.append(
                LowAuthorityObjectRead(
                    domain=domain,
                    sub_domain=sub_domain,
                    current_value=current_value,
                    authority_score=authority_score,
                    reason="Low authority score",
                )
            )
            seen_slots.add(slot)

    return sorted(
        low_objects,
        key=lambda obj: (obj.authority_score, obj.domain, obj.sub_domain),
    )


def _build_authority_used(
    changed_object: ChangedObjectRead | None,
    affected_objects: list[AffectedObjectRead],
    changed_source_system: str | None = None,
) -> list[AuthorityUsedRead]:
    if changed_object is None:
        return []

    authority_used = [
        AuthorityUsedRead(
            domain=changed_object.domain,
            sub_domain=changed_object.sub_domain,
            authority_score=changed_object.authority_score,
            source_system=changed_source_system or "unknown",
        )
    ]

    for obj in affected_objects:
        authority_used.append(
            AuthorityUsedRead(
                domain=obj.domain,
                sub_domain=obj.sub_domain,
                authority_score=obj.authority_score,
                source_system=obj.source_system,
            )
        )

    return authority_used


def simulate_decision_change(
    db: Session,
    change: DecisionChangeInput,
) -> DecisionSimulationResponse:
    changed_object = find_changed_object(
        db,
        change.domain,
        change.sub_domain,
        change.new_value,
    )
    source_item = _pick_highest_priority_item(
        _active_items_for_slot(db, change.domain, change.sub_domain)
    )
    affected_objects = find_affected_objects(db, change.domain, change.sub_domain)
    recommended_checks = build_recommended_checks(change, affected_objects)
    decision_readiness = calculate_decision_readiness(changed_object, affected_objects)

    return DecisionSimulationResponse(
        decision=_decision_label(change.domain, change.sub_domain),
        changed_object=changed_object,
        affected_objects=affected_objects,
        recommended_checks=recommended_checks,
        authority_used=_build_authority_used(
            changed_object,
            affected_objects,
            source_item.source_system if source_item else None,
        ),
        decision_readiness=decision_readiness,
    )
