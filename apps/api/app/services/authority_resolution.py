from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.schemas.authority_resolution import CurrentTruthRead, ResolutionStatus
from app.services.decision_simulation import is_incomplete_knowledge

Slot = tuple[str, str]

SOURCE_AUTHORITY: dict[str, tuple[str, int]] = {
    "founder_input": ("Founder Input", 100),
    "notion": ("Notion", 95),
    "stripe": ("Stripe", 95),
    "hubspot": ("HubSpot", 92),
    "linear": ("Linear", 92),
    "crm": ("CRM", 90),
    "public_website": ("Website", 80),
    "website": ("Website", 80),
    "website_import": ("Public Sources", 70),
}

PUBLIC_SOURCE_SYSTEMS = {
    "public_website",
    "website",
    "website_import",
}

DEFAULT_SOURCE_NAME = "Unknown Source"
DEFAULT_AUTHORITY_SCORE = 50

MISSING_KNOWLEDGE_REASON = (
    "Authority AI does not have enough non-placeholder knowledge to establish "
    "current truth for this business object."
)


@dataclass
class _ResolvedSource:
    item: KnowledgeItem
    display_source: str
    authority_score: int
    content: str
    updated_at: datetime
    is_public: bool


def is_placeholder_value(value: str) -> bool:
    return is_incomplete_knowledge(value)


def _normalize_content(content: str) -> str:
    return content.strip()


def _source_name_and_score(source_system: str) -> tuple[str, int]:
    return SOURCE_AUTHORITY.get(
        source_system.lower(),
        (source_system.replace("_", " ").title(), DEFAULT_AUTHORITY_SCORE),
    )


def _is_public_source(source_system: str) -> bool:
    return source_system.lower() in PUBLIC_SOURCE_SYSTEMS


def _to_resolved_source(item: KnowledgeItem) -> _ResolvedSource:
    display_source, authority_score = _source_name_and_score(item.source_system)
    updated_at = item.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)

    return _ResolvedSource(
        item=item,
        display_source=display_source,
        authority_score=authority_score,
        content=_normalize_content(item.content),
        updated_at=updated_at,
        is_public=_is_public_source(item.source_system),
    )


def _pick_winner(sources: list[_ResolvedSource]) -> _ResolvedSource:
    return max(
        sources,
        key=lambda source: (
            source.authority_score,
            source.updated_at.timestamp(),
            not source.is_public,
        ),
    )


def _missing_knowledge_result(domain: str, sub_domain: str) -> CurrentTruthRead:
    return CurrentTruthRead(
        domain=domain,
        sub_domain=sub_domain,
        current_truth=None,
        chosen_source=None,
        authority_score=0,
        supporting_sources=[],
        conflicting_sources=[],
        resolution_confidence=0,
        resolution_status="missing_knowledge",
        resolution_reason=MISSING_KNOWLEDGE_REASON,
    )


def _resolution_confidence(
    winner: _ResolvedSource,
    supporting_sources: list[str],
    conflicting_sources: list[str],
) -> int:
    if conflicting_sources:
        return max(winner.authority_score - 10, 0)

    if supporting_sources:
        return min(winner.authority_score + 5, 100)

    return winner.authority_score


def _resolution_status(conflicting_sources: list[str]) -> ResolutionStatus:
    if conflicting_sources:
        return "conflict_review"
    return "resolved"


def _resolution_reason(
    winner: _ResolvedSource,
    supporting_sources: list[str],
    conflicting_sources: list[str],
) -> str:
    if conflicting_sources:
        joined = ", ".join(conflicting_sources)
        return (
            f"Current truth selected because {winner.display_source} has higher "
            f"authority than conflicting sources: {joined}."
        )

    if supporting_sources:
        joined = ", ".join(supporting_sources)
        return (
            f"Current truth selected because {winner.display_source} is the "
            "highest-authority available source and "
            f"{joined} corroborates the same value."
        )

    return (
        f"Current truth selected because {winner.display_source} is the "
        "highest-authority available source and no conflicting non-placeholder "
        "sources were found."
    )


def _resolve_group(items: list[KnowledgeItem]) -> CurrentTruthRead:
    domain = items[0].domain
    sub_domain = items[0].sub_domain
    sources = [_to_resolved_source(item) for item in items]
    substantive_sources = [
        source for source in sources if not is_placeholder_value(source.content)
    ]

    if not substantive_sources:
        return _missing_knowledge_result(domain, sub_domain)

    winner = _pick_winner(substantive_sources)
    winner_content = winner.content

    supporting_sources = sorted(
        {
            source.display_source
            for source in substantive_sources
            if source.content == winner_content
            and source.display_source != winner.display_source
        }
    )

    conflicting_sources = sorted(
        {
            source.display_source
            for source in substantive_sources
            if source.content != winner_content
            and (
                source.authority_score < winner.authority_score
                or (
                    source.authority_score == winner.authority_score
                    and source.item.id != winner.item.id
                )
            )
        }
    )

    status = _resolution_status(conflicting_sources)
    confidence = _resolution_confidence(
        winner,
        supporting_sources,
        conflicting_sources,
    )

    return CurrentTruthRead(
        domain=domain,
        sub_domain=sub_domain,
        current_truth=winner_content,
        chosen_source=winner.display_source,
        authority_score=winner.authority_score,
        supporting_sources=supporting_sources,
        conflicting_sources=conflicting_sources,
        resolution_confidence=confidence,
        resolution_status=status,
        resolution_reason=_resolution_reason(
            winner,
            supporting_sources,
            conflicting_sources,
        ),
    )


def _group_active_items(db: Session) -> dict[Slot, list[KnowledgeItem]]:
    items = list(
        db.scalars(
            select(KnowledgeItem)
            .where(KnowledgeItem.is_active.is_(True))
            .order_by(
                KnowledgeItem.domain,
                KnowledgeItem.sub_domain,
                KnowledgeItem.source_priority,
            )
        ).all()
    )

    groups: dict[Slot, list[KnowledgeItem]] = {}
    for item in items:
        groups.setdefault((item.domain, item.sub_domain), []).append(item)
    return groups


def resolve_current_truth(db: Session) -> list[CurrentTruthRead]:
    groups = _group_active_items(db)
    resolved: list[CurrentTruthRead] = []

    for slot in sorted(groups.keys()):
        resolved.append(_resolve_group(groups[slot]))

    return resolved
