from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.schemas.authority_object import AuthorityObject
from app.schemas.company import (
    CompanyRefreshResponse,
    RefreshChangeRead,
    RefreshHistoryEntry,
    RefreshHistoryResponse,
    RefreshSummaryRead,
)
from app.services.authority_objects import (
    PUBLIC_KNOWLEDGE_OBJECT_COUNT,
    PUBLIC_SOURCE_SYSTEMS,
    AuthorityObjectDiff,
    authority_object_from_knowledge_item,
    build_snapshot_authority_objects,
    build_supplemental_authority_objects,
    compare_authority_objects,
    knowledge_item_from_authority_object,
)
from app.services.company import _snapshot_from_extracted
from app.services.website_extractor import extract_public_knowledge, normalize_website_url

_refresh_history: list[RefreshHistoryEntry] = []


def _load_active_public_authority_objects(db: Session) -> list[AuthorityObject]:
    items = db.scalars(
        select(KnowledgeItem).where(
            KnowledgeItem.source_system.in_(PUBLIC_SOURCE_SYSTEMS),
            KnowledgeItem.is_active.is_(True),
        )
    ).all()
    return [authority_object_from_knowledge_item(item) for item in items]


def _build_refresh_authority_objects(extracted, normalized_url: str) -> list[AuthorityObject]:
    snapshot = _snapshot_from_extracted(extracted, normalized_url)
    authority_objects = build_snapshot_authority_objects(snapshot)
    authority_objects.extend(build_supplemental_authority_objects(snapshot))
    return authority_objects[:PUBLIC_KNOWLEDGE_OBJECT_COUNT]


def _load_public_items_by_slot(db: Session) -> dict[tuple[str, str], KnowledgeItem]:
    items = db.scalars(
        select(KnowledgeItem).where(
            KnowledgeItem.source_system.in_(PUBLIC_SOURCE_SYSTEMS),
        )
    ).all()
    return {(item.domain, item.sub_domain): item for item in items}


def _change_records_from_diff(diff: AuthorityObjectDiff) -> list[RefreshChangeRead]:
    changes: list[RefreshChangeRead] = []

    for obj in diff["new"]:
        changes.append(
            RefreshChangeRead(
                type="new",
                domain=obj.domain,
                sub_domain=obj.sub_domain,
                before=None,
                after=obj.value,
                authority_score_after=obj.authority_score,
            )
        )

    for old_obj, new_obj in diff["updated"]:
        changes.append(
            RefreshChangeRead(
                type="updated",
                domain=new_obj.domain,
                sub_domain=new_obj.sub_domain,
                before=old_obj.value,
                after=new_obj.value,
                authority_score_before=None,
                authority_score_after=new_obj.authority_score,
            )
        )

    for obj in diff["removed"]:
        changes.append(
            RefreshChangeRead(
                type="removed",
                domain=obj.domain,
                sub_domain=obj.sub_domain,
                before=obj.value,
                after=None,
            )
        )

    return changes


def _summary_from_diff(diff: AuthorityObjectDiff) -> RefreshSummaryRead:
    return RefreshSummaryRead(
        new=len(diff["new"]),
        updated=len(diff["updated"]),
        removed=len(diff["removed"]),
        unchanged=len(diff["unchanged"]),
    )


def _apply_refresh_changes(
    db: Session,
    diff: AuthorityObjectDiff,
    now: datetime,
) -> None:
    items_by_slot = _load_public_items_by_slot(db)

    for new_obj in diff["new"]:
        existing = items_by_slot.get((new_obj.domain, new_obj.sub_domain))
        if existing is None:
            item = knowledge_item_from_authority_object(new_obj, now)
            db.add(item)
            items_by_slot[(new_obj.domain, new_obj.sub_domain)] = item
            continue

        existing.content = new_obj.value
        existing.source_url = new_obj.source_url
        existing.updated_at = now
        existing.is_active = True

    for old_obj, new_obj in diff["updated"]:
        item = items_by_slot.get((old_obj.domain, old_obj.sub_domain))
        if item is None:
            item = knowledge_item_from_authority_object(new_obj, now)
            db.add(item)
            items_by_slot[(new_obj.domain, new_obj.sub_domain)] = item
            continue

        item.content = new_obj.value
        item.source_url = new_obj.source_url
        item.updated_at = now
        item.is_active = True

    for old_obj in diff["removed"]:
        item = items_by_slot.get((old_obj.domain, old_obj.sub_domain))
        if item is None or not item.is_active:
            continue

        item.is_active = False
        item.updated_at = now


def refresh_company_brain(db: Session, website_url: str) -> CompanyRefreshResponse:
    normalized_url = normalize_website_url(website_url)
    extracted = extract_public_knowledge(normalized_url)

    old_objects = _load_active_public_authority_objects(db)
    new_objects = _build_refresh_authority_objects(extracted, normalized_url)
    diff = compare_authority_objects(old_objects, new_objects)

    now = datetime.now(timezone.utc)
    _apply_refresh_changes(db, diff, now)
    db.commit()

    summary = _summary_from_diff(diff)
    changes = _change_records_from_diff(diff)
    response = CompanyRefreshResponse(
        company=extracted.company_name,
        summary=summary,
        changes=changes,
    )

    _refresh_history.insert(
        0,
        RefreshHistoryEntry(time=now, summary=summary),
    )

    return response


def get_refresh_history() -> RefreshHistoryResponse:
    return RefreshHistoryResponse(refreshes=list(_refresh_history))
