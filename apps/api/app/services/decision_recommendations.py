from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.models.knowledge_relationship import KnowledgeRelationship
from app.schemas.decision import (
    DecisionRecommendationRead,
    DecisionRecommendationsResponse,
    DecisionRecommendationsSummaryRead,
    RecommendationSourceObjectRead,
)
from app.services.brain import _pick_highest_priority_item
from app.services.decision_simulation import (
    FALLBACK_RELATIONSHIPS,
    infer_authority_score,
    is_incomplete_knowledge,
)

Slot = tuple[str, str]
Priority = str

HIGH_PRIORITY_SLOTS: list[Slot] = [
    ("financial", "mrr"),
    ("financial", "runway"),
    ("decisions", "pricing"),
    ("pipeline", "objection"),
]

MEDIUM_PRIORITY_SLOTS: list[Slot] = [
    ("mission", "icp"),
    ("mission", "product"),
    ("engineering", "blocker"),
]

COMPANY_PROFILE_SLOTS: list[Slot] = [
    ("company", "stage"),
    ("company", "employees"),
    ("company", "funding"),
]

PUBLIC_SOURCE_SLOTS: list[Slot] = [
    ("source", "public_pricing_page"),
    ("source", "public_docs_page"),
    ("source", "public_about_page"),
]

STALE_DAYS: dict[Slot, int] = {
    ("financial", "mrr"): 30,
    ("financial", "runway"): 30,
    ("pipeline", "objection"): 30,
    ("engineering", "blocker"): 60,
    ("mission", "product"): 90,
    ("mission", "icp"): 90,
}
DEFAULT_STALE_DAYS = 180

PRICING_RELATIONSHIP_TARGETS: list[Slot] = [
    ("financial", "mrr"),
    ("pipeline", "objection"),
    ("mission", "icp"),
]

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

SLOT_IMPORTANCE: dict[Slot, int] = {
    ("financial", "mrr"): 10,
    ("financial", "runway"): 10,
    ("pipeline", "objection"): 9,
    ("decisions", "pricing"): 8,
    ("engineering", "blocker"): 8,
    ("mission", "icp"): 6,
    ("mission", "product"): 5,
    ("company", "stage"): 3,
    ("company", "employees"): 3,
    ("company", "funding"): 3,
}

SLOT_AFFECTED_DECISIONS: dict[Slot, list[str]] = {
    ("financial", "mrr"): ["MRR", "Runway", "Finance", "Pricing"],
    ("financial", "runway"): ["Hiring", "Fundraising", "Burn", "Finance"],
    ("decisions", "pricing"): ["Pricing", "MRR", "Sales", "ICP"],
    ("pipeline", "objection"): ["Pricing", "Sales", "ICP", "Product"],
    ("mission", "icp"): ["Sales", "Pricing", "Product", "Positioning"],
    ("mission", "product"): ["Product", "Sales", "Positioning"],
    ("engineering", "blocker"): ["Product", "Engineering", "Delivery"],
    ("company", "stage"): ["Positioning", "Fundraising", "Hiring"],
    ("company", "employees"): ["Hiring", "Team", "Culture"],
    ("company", "funding"): ["Fundraising", "Finance", "Runway"],
}


@dataclass
class _DraftRecommendation:
    dedupe_key: tuple
    priority: Priority
    title: str
    reason: str
    impact: str
    affected_decisions: list[str]
    recommended_action: str
    source_objects: list[RecommendationSourceObjectRead] = field(default_factory=list)
    domain_importance: int = 0


def _slot_importance(slot: Slot) -> int:
    return SLOT_IMPORTANCE.get(slot, 1)


def _affected_decisions(slot: Slot) -> list[str]:
    return SLOT_AFFECTED_DECISIONS.get(
        slot,
        [slot[1].replace("_", " ").title()],
    )


def _source_object(item: KnowledgeItem) -> RecommendationSourceObjectRead:
    return RecommendationSourceObjectRead(
        domain=item.domain,
        sub_domain=item.sub_domain,
        current_value=item.content,
        source_system=item.source_system,
        authority_score=infer_authority_score(item),
    )


def _load_active_knowledge_items(db: Session) -> list[KnowledgeItem]:
    items = list(
        db.scalars(
            select(KnowledgeItem).order_by(
                KnowledgeItem.source_priority,
                KnowledgeItem.trust_rank,
            )
        ).all()
    )
    return [item for item in items if getattr(item, "is_active", True) is not False]


def _build_slot_indexes(
    items: list[KnowledgeItem],
) -> tuple[dict[Slot, list[KnowledgeItem]], dict[Slot, KnowledgeItem]]:
    all_items_by_slot: dict[Slot, list[KnowledgeItem]] = {}
    for item in items:
        all_items_by_slot.setdefault((item.domain, item.sub_domain), []).append(item)

    items_by_slot = {
        slot: picked
        for slot, slot_items in all_items_by_slot.items()
        if (picked := _pick_highest_priority_item(slot_items)) is not None
    }
    return all_items_by_slot, items_by_slot


def _detect_placeholder_items(items: list[KnowledgeItem]) -> list[tuple[str, str, str]]:
    placeholders: list[tuple[str, str, str]] = []
    for item in items:
        if is_incomplete_knowledge(item.content):
            placeholders.append((item.domain, item.sub_domain, item.content))
    return placeholders


def _representative_item_for_slot(
    all_items_by_slot: dict[Slot, list[KnowledgeItem]],
    slot: Slot,
) -> KnowledgeItem | None:
    slot_items = all_items_by_slot.get(slot, [])
    if not slot_items:
        return None

    for item in sorted(
        slot_items,
        key=lambda candidate: (candidate.source_priority, candidate.trust_rank),
    ):
        if is_incomplete_knowledge(item.content):
            return item

    return _pick_highest_priority_item(slot_items)


def _slot_has_gap(
    all_items_by_slot: dict[Slot, list[KnowledgeItem]],
    slot: Slot,
) -> tuple[bool, KnowledgeItem | None]:
    slot_items = all_items_by_slot.get(slot, [])
    if not slot_items:
        return True, None

    incomplete_item = next(
        (item for item in slot_items if is_incomplete_knowledge(item.content)),
        None,
    )
    if incomplete_item is not None:
        return True, incomplete_item

    return False, _pick_highest_priority_item(slot_items)


def _is_stale(item: KnowledgeItem, slot: Slot, now: datetime) -> bool:
    updated_at = item.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)

    threshold_days = STALE_DAYS.get(slot, DEFAULT_STALE_DAYS)
    return (now - updated_at).days > threshold_days


def _slot_priority(slot: Slot) -> Priority:
    if slot in HIGH_PRIORITY_SLOTS:
        return "high"
    if slot in MEDIUM_PRIORITY_SLOTS:
        return "medium"
    return "low"


def _add_recommendation(
    drafts: dict[tuple, _DraftRecommendation],
    draft: _DraftRecommendation,
) -> None:
    existing = drafts.get(draft.dedupe_key)
    if existing is None:
        drafts[draft.dedupe_key] = draft
        return

    if PRIORITY_ORDER[draft.priority] < PRIORITY_ORDER[existing.priority]:
        drafts[draft.dedupe_key] = draft


def _missing_recommendation(slot: Slot) -> _DraftRecommendation:
    if slot == ("financial", "runway"):
        return _DraftRecommendation(
            dedupe_key=("missing", *slot),
            priority="high",
            title="Add runway knowledge",
            reason="Runway is required for hiring, fundraising, and burn decisions.",
            impact="High",
            affected_decisions=_affected_decisions(slot),
            recommended_action="Add current runway or connect the financial source of truth.",
            domain_importance=_slot_importance(slot),
        )

    if slot == ("financial", "mrr"):
        return _DraftRecommendation(
            dedupe_key=("missing", *slot),
            priority="high",
            title="Add MRR knowledge",
            reason="MRR is required for revenue, runway, and pricing decisions.",
            impact="High",
            affected_decisions=_affected_decisions(slot),
            recommended_action="Add current MRR or connect Stripe.",
            domain_importance=_slot_importance(slot),
        )

    if slot == ("pipeline", "objection"):
        return _DraftRecommendation(
            dedupe_key=("missing", *slot),
            priority="high",
            title="Add customer objection knowledge",
            reason="Customer objections are required for pricing and sales decisions.",
            impact="High",
            affected_decisions=_affected_decisions(slot),
            recommended_action="Add current objections or connect HubSpot.",
            domain_importance=_slot_importance(slot),
        )

    if slot == ("decisions", "pricing"):
        return _DraftRecommendation(
            dedupe_key=("missing", *slot),
            priority="high",
            title="Add pricing knowledge",
            reason="Pricing is required for revenue, sales, and ICP decisions.",
            impact="High",
            affected_decisions=_affected_decisions(slot),
            recommended_action="Add pricing details or connect the source system that owns pricing.",
            domain_importance=_slot_importance(slot),
        )

    label = slot[1].replace("_", " ").title()
    return _DraftRecommendation(
        dedupe_key=("missing", *slot),
        priority=_slot_priority(slot),
        title=f"Add {label.lower()} knowledge",
        reason=f"{label} knowledge is missing from the Company Brain.",
        impact=_slot_priority(slot).title(),
        affected_decisions=_affected_decisions(slot),
        recommended_action=f"Add {label.lower()} knowledge or connect its source of truth.",
        domain_importance=_slot_importance(slot),
    )


def _incomplete_recommendation(
    slot: Slot,
    item: KnowledgeItem,
) -> _DraftRecommendation:
    if slot == ("decisions", "pricing"):
        return _DraftRecommendation(
            dedupe_key=("incomplete", *slot),
            priority="high",
            title="Complete pricing knowledge",
            reason=(
                "Pricing knowledge is incomplete. Authority AI only knows that a "
                "pricing page exists, not the actual pricing."
            ),
            impact="High",
            affected_decisions=_affected_decisions(slot),
            recommended_action=(
                "Update pricing details or connect the source system that owns pricing."
            ),
            source_objects=[_source_object(item)],
            domain_importance=_slot_importance(slot),
        )

    label = slot[1].replace("_", " ").title()
    return _DraftRecommendation(
        dedupe_key=("incomplete", *slot),
        priority=_slot_priority(slot),
        title=f"Complete {label.lower()} knowledge",
        reason=f"{label} knowledge is incomplete or contains placeholder values.",
        impact=_slot_priority(slot).title(),
        affected_decisions=_affected_decisions(slot),
        recommended_action=f"Update {label.lower()} details or connect its source of truth.",
        source_objects=[_source_object(item)],
        domain_importance=_slot_importance(slot),
    )


def _stale_recommendation(
    slot: Slot,
    item: KnowledgeItem,
) -> _DraftRecommendation:
    if slot == ("pipeline", "objection"):
        return _DraftRecommendation(
            dedupe_key=("stale", *slot),
            priority="high",
            title="Refresh customer objections",
            reason=(
                "Customer objection data is stale and may no longer reflect "
                "current sales friction."
            ),
            impact="High",
            affected_decisions=_affected_decisions(slot),
            recommended_action="Refresh CRM objections or connect HubSpot.",
            source_objects=[_source_object(item)],
            domain_importance=_slot_importance(slot),
        )

    label = slot[1].replace("_", " ").title()
    priority: Priority = "high" if slot in HIGH_PRIORITY_SLOTS else "medium"
    return _DraftRecommendation(
        dedupe_key=("stale", *slot),
        priority=priority,
        title=f"Refresh {label.lower()} knowledge",
        reason=f"{label} knowledge is stale and may no longer reflect current reality.",
        impact=priority.title(),
        affected_decisions=_affected_decisions(slot),
        recommended_action=f"Refresh {label.lower()} or reconnect its source of truth.",
        source_objects=[_source_object(item)],
        domain_importance=_slot_importance(slot),
    )


def _low_authority_recommendation(
    slot: Slot,
    item: KnowledgeItem,
) -> _DraftRecommendation:
    affected = _affected_decisions(slot)
    downstream_count = len(FALLBACK_RELATIONSHIPS.get(slot, []))
    priority: Priority = "high" if downstream_count >= 2 else _slot_priority(slot)

    label = slot[1].replace("_", " ").title()
    return _DraftRecommendation(
        dedupe_key=("low_authority", *slot),
        priority=priority,
        title=f"Improve {label.lower()} knowledge authority",
        reason=(
            f"{label} knowledge has low inferred authority and weakens decision readiness."
        ),
        impact=priority.title(),
        affected_decisions=affected,
        recommended_action=(
            f"Connect a stronger source of truth for {label.lower()} knowledge."
        ),
        source_objects=[_source_object(item)],
        domain_importance=_slot_importance(slot),
    )


def _evaluate_slot(
    drafts: dict[tuple, _DraftRecommendation],
    slot: Slot,
    all_items_by_slot: dict[Slot, list[KnowledgeItem]],
    now: datetime,
) -> None:
    has_gap, item = _slot_has_gap(all_items_by_slot, slot)

    if item is None:
        _add_recommendation(drafts, _missing_recommendation(slot))
        return

    if has_gap and is_incomplete_knowledge(item.content):
        _add_recommendation(drafts, _incomplete_recommendation(slot, item))
        return

    if _is_stale(item, slot, now):
        _add_recommendation(drafts, _stale_recommendation(slot, item))

    if infer_authority_score(item) < 60:
        _add_recommendation(drafts, _low_authority_recommendation(slot, item))


def _evaluate_company_profile(
    drafts: dict[tuple, _DraftRecommendation],
    all_items_by_slot: dict[Slot, list[KnowledgeItem]],
) -> None:
    profile_gaps: list[RecommendationSourceObjectRead] = []

    for slot in COMPANY_PROFILE_SLOTS:
        has_gap, item = _slot_has_gap(all_items_by_slot, slot)
        if not has_gap:
            continue

        if item is not None:
            profile_gaps.append(_source_object(item))
        else:
            profile_gaps.append(
                RecommendationSourceObjectRead(
                    domain=slot[0],
                    sub_domain=slot[1],
                    current_value="Unknown",
                    source_system="missing",
                    authority_score=0,
                )
            )

    if not profile_gaps:
        return

    _add_recommendation(
        drafts,
        _DraftRecommendation(
            dedupe_key=("company_profile",),
            priority="low",
            title="Complete company profile knowledge",
            reason="Some public company profile fields are unknown.",
            impact="Low",
            affected_decisions=["Positioning", "Fundraising", "Hiring"],
            recommended_action="Review company stage, employees, and funding.",
            source_objects=profile_gaps,
            domain_importance=3,
        ),
    )


def _evaluate_public_source_links(
    drafts: dict[tuple, _DraftRecommendation],
    items_by_slot: dict[Slot, KnowledgeItem],
) -> None:
    missing_links = [
        slot for slot in PUBLIC_SOURCE_SLOTS if slot not in items_by_slot
    ]
    if not missing_links:
        return

    _add_recommendation(
        drafts,
        _DraftRecommendation(
            dedupe_key=("public_source_links",),
            priority="low",
            title="Connect public source links",
            reason="Some authoritative public source links are missing from the Company Brain.",
            impact="Low",
            affected_decisions=["Pricing", "Product", "Positioning"],
            recommended_action="Refresh the public website or add missing public source links.",
            source_objects=[
                RecommendationSourceObjectRead(
                    domain=slot[0],
                    sub_domain=slot[1],
                    current_value="Missing",
                    source_system="missing",
                    authority_score=0,
                )
                for slot in missing_links
            ],
            domain_importance=2,
        ),
    )


def _evaluate_pricing_relationships(
    drafts: dict[tuple, _DraftRecommendation],
    items_by_slot: dict[Slot, KnowledgeItem],
    db: Session,
) -> None:
    pricing_item = items_by_slot.get(("decisions", "pricing"))
    if pricing_item is None:
        return

    relationships = db.scalars(
        select(KnowledgeRelationship).where(
            KnowledgeRelationship.source_knowledge_id == pricing_item.id
        )
    ).all()

    if not relationships:
        missing_targets = PRICING_RELATIONSHIP_TARGETS
    else:
        target_ids = {relationship.target_knowledge_id for relationship in relationships}
        target_items = list(
            db.scalars(
                select(KnowledgeItem).where(KnowledgeItem.id.in_(target_ids))
            ).all()
        )
        linked_slots = {(item.domain, item.sub_domain) for item in target_items}
        missing_targets = [
            slot for slot in PRICING_RELATIONSHIP_TARGETS if slot not in linked_slots
        ]

    critical_missing = [
        slot
        for slot in missing_targets
        if slot in {("financial", "mrr"), ("pipeline", "objection")}
    ]
    if not critical_missing:
        return

    _add_recommendation(
        drafts,
        _DraftRecommendation(
            dedupe_key=("missing_relationships", "decisions", "pricing"),
            priority="medium",
            title="Add pricing decision relationships",
            reason=(
                "Pricing exists, but Authority AI cannot fully trace its "
                "downstream business impact."
            ),
            impact="Medium",
            affected_decisions=["Pricing", "MRR", "Sales"],
            recommended_action=(
                "Connect pricing to MRR, customer objections, and ICP."
            ),
            source_objects=[_source_object(pricing_item)],
            domain_importance=_slot_importance(("decisions", "pricing")),
        ),
    )


def _ensure_core_placeholder_recommendations(
    drafts: dict[tuple, _DraftRecommendation],
    all_items_by_slot: dict[Slot, list[KnowledgeItem]],
) -> None:
    pricing_item = _representative_item_for_slot(
        all_items_by_slot,
        ("decisions", "pricing"),
    )
    if pricing_item is not None and is_incomplete_knowledge(pricing_item.content):
        _add_recommendation(
            drafts,
            _incomplete_recommendation(("decisions", "pricing"), pricing_item),
        )

    profile_gaps: list[RecommendationSourceObjectRead] = []
    for slot in COMPANY_PROFILE_SLOTS:
        has_gap, item = _slot_has_gap(all_items_by_slot, slot)
        if not has_gap:
            continue
        if item is not None:
            profile_gaps.append(_source_object(item))
        else:
            profile_gaps.append(
                RecommendationSourceObjectRead(
                    domain=slot[0],
                    sub_domain=slot[1],
                    current_value="Unknown",
                    source_system="missing",
                    authority_score=0,
                )
            )

    if profile_gaps:
        _add_recommendation(
            drafts,
            _DraftRecommendation(
                dedupe_key=("company_profile",),
                priority="low",
                title="Complete company profile knowledge",
                reason="Some public company profile fields are unknown.",
                impact="Low",
                affected_decisions=["Positioning", "Fundraising", "Hiring"],
                recommended_action="Review company stage, employees, and funding.",
                source_objects=profile_gaps,
                domain_importance=3,
            ),
        )


def _sort_recommendations(
    drafts: dict[tuple, _DraftRecommendation],
) -> list[DecisionRecommendationRead]:
    sorted_drafts = sorted(
        drafts.values(),
        key=lambda draft: (
            PRIORITY_ORDER[draft.priority],
            -len(draft.affected_decisions),
            -draft.domain_importance,
            draft.title,
        ),
    )
    return [
        DecisionRecommendationRead(
            priority=draft.priority,
            title=draft.title,
            reason=draft.reason,
            impact=draft.impact,
            affected_decisions=draft.affected_decisions,
            recommended_action=draft.recommended_action,
            source_objects=draft.source_objects,
        )
        for draft in sorted_drafts
    ]


def generate_decision_recommendations(db: Session) -> DecisionRecommendationsResponse:
    now = datetime.now(timezone.utc)
    active_items = _load_active_knowledge_items(db)
    all_items_by_slot, items_by_slot = _build_slot_indexes(active_items)
    placeholder_items = _detect_placeholder_items(active_items)

    print(f"KnowledgeItems loaded: {len(active_items)}")
    print(f"detected placeholder items: {placeholder_items}")

    drafts: dict[tuple, _DraftRecommendation] = {}

    for slot in HIGH_PRIORITY_SLOTS + MEDIUM_PRIORITY_SLOTS:
        _evaluate_slot(drafts, slot, all_items_by_slot, now)

    _evaluate_company_profile(drafts, all_items_by_slot)
    _ensure_core_placeholder_recommendations(drafts, all_items_by_slot)
    _evaluate_public_source_links(drafts, items_by_slot)
    _evaluate_pricing_relationships(drafts, items_by_slot, db)

    recommendations = _sort_recommendations(drafts)
    print(f"recommendations generated: {len(recommendations)}")

    summary = DecisionRecommendationsSummaryRead(
        high=sum(1 for rec in recommendations if rec.priority == "high"),
        medium=sum(1 for rec in recommendations if rec.priority == "medium"),
        low=sum(1 for rec in recommendations if rec.priority == "low"),
        total=len(recommendations),
    )

    return DecisionRecommendationsResponse(
        recommendations=recommendations,
        summary=summary,
    )
