import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.schemas.integrations import NotionImportResponse
from app.services.brain import _pick_highest_priority_item

NOTION_WORKSPACE_PATH = (
    Path(__file__).resolve().parent.parent / "demo" / "notion_workspace.json"
)

NOTION_SOURCE_SYSTEM = "notion"
NOTION_SOURCE_PRIORITY = 95
NOTION_TRUST_RANK = 5

PAGE_SLOT_MAPPINGS: dict[str, tuple[str, str]] = {
    "Pricing Strategy": ("decisions", "pricing"),
    "Current Runway": ("financial", "runway"),
    "Engineering Blockers": ("engineering", "blocker"),
    "Customer Feedback": ("pipeline", "objection"),
    "ICP": ("mission", "icp"),
    "Hiring Plan": ("team", "hiring"),
    "Product Roadmap": ("product", "roadmap"),
    "Fundraising Notes": ("financial", "fundraising"),
}


def _parse_last_edited_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _load_demo_workspace() -> dict:
    return json.loads(NOTION_WORKSPACE_PATH.read_text(encoding="utf-8"))


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


def _find_existing_slot_item(
    db: Session,
    domain: str,
    sub_domain: str,
) -> KnowledgeItem | None:
    return _pick_highest_priority_item(_active_items_for_slot(db, domain, sub_domain))


def _upsert_notion_knowledge_item(
    db: Session,
    *,
    domain: str,
    sub_domain: str,
    content: str,
    source_url: str,
    last_edited_time: datetime,
) -> tuple[bool, bool]:
    existing = _find_existing_slot_item(db, domain, sub_domain)

    if existing is None:
        db.add(
            KnowledgeItem(
                domain=domain,
                sub_domain=sub_domain,
                content=content,
                source_system=NOTION_SOURCE_SYSTEM,
                source_url=source_url,
                source_priority=NOTION_SOURCE_PRIORITY,
                trust_rank=NOTION_TRUST_RANK,
                allowed_roles=["founder", "admin", "member"],
                created_at=last_edited_time,
                updated_at=last_edited_time,
                is_active=True,
            )
        )
        return True, False

    existing.content = content
    existing.source_system = NOTION_SOURCE_SYSTEM
    existing.source_url = source_url
    existing.source_priority = NOTION_SOURCE_PRIORITY
    existing.trust_rank = NOTION_TRUST_RANK
    existing.updated_at = last_edited_time
    existing.is_active = True
    return False, True


def import_demo_notion_workspace(db: Session) -> NotionImportResponse:
    workspace = _load_demo_workspace()
    pages = workspace.get("pages", [])

    knowledge_items_created = 0
    knowledge_items_updated = 0

    for page in pages:
        title = page["title"]
        slot = PAGE_SLOT_MAPPINGS.get(title)
        if slot is None:
            continue

        domain, sub_domain = slot
        created, updated = _upsert_notion_knowledge_item(
            db,
            domain=domain,
            sub_domain=sub_domain,
            content=page["content"],
            source_url=page.get("source_url", ""),
            last_edited_time=_parse_last_edited_time(page["last_edited_time"]),
        )

        if created:
            knowledge_items_created += 1
        if updated:
            knowledge_items_updated += 1

    db.commit()

    pages_imported = len(pages)
    company_brain_strengthened = (knowledge_items_created + knowledge_items_updated) > 0

    return NotionImportResponse(
        pages_imported=pages_imported,
        knowledge_items_created=knowledge_items_created,
        knowledge_items_updated=knowledge_items_updated,
        company_brain_strengthened=company_brain_strengthened,
    )
