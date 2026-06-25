from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.schemas.company import (
    AnalyzeWebsiteResponse,
    CompanySnapshot,
    CurrentBrainResponse,
    GenerateBrainRequest,
    GenerateBrainResponse,
    PrivateKnowledge,
)
from app.schemas.knowledge_item import KnowledgeItemRead

MISSING_PRIVATE_FIELDS = [
    "current_mrr",
    "current_runway",
    "top_customer_objection",
    "current_engineering_blocker",
    "founder_dependent_knowledge",
]

PUBLIC_KNOWLEDGE_OBJECT_COUNT = 19

WEBSITE_IMPORT = "website_import"
FOUNDER_INPUT = "founder_input"
IMPORT_SOURCE_PRIORITY = 10
IMPORT_TRUST_RANK = 3

PUBLIC_SNAPSHOT_MAPPINGS: list[tuple[str, str, str]] = [
    ("company_name", "mission", "company"),
    ("industry", "mission", "industry"),
    ("product", "mission", "product"),
    ("icp", "mission", "icp"),
    ("pricing", "decisions", "pricing"),
    ("stage", "company", "stage"),
    ("employees", "company", "employees"),
    ("funding", "company", "funding"),
    ("description", "mission", "description"),
]

PRIVATE_KNOWLEDGE_MAPPINGS: list[tuple[str, str, str, str]] = [
    (
        "current_mrr",
        "financial",
        "mrr",
        "Current MRR is {value}",
    ),
    (
        "current_runway",
        "financial",
        "runway",
        "Current runway is {value}",
    ),
    (
        "top_customer_objection",
        "pipeline",
        "objection",
        "{value}",
    ),
    (
        "current_engineering_blocker",
        "engineering",
        "blocker",
        "{value}",
    ),
    (
        "founder_dependent_knowledge",
        "operations",
        "founder_dependency",
        "{value}",
    ),
]

_current_company_brain: dict | None = None


def _forgepilot_snapshot(website_url: str) -> CompanySnapshot:
    return CompanySnapshot(
        company_name="ForgePilot",
        industry="Industrial SaaS",
        product="AI-powered workflow automation for manufacturing teams",
        icp="Mid-market manufacturers with 100-500 employees",
        pricing="Custom enterprise pricing starting at $2,500/month",
        stage="Series A",
        employees="45",
        funding="$8M Series A",
        website=website_url,
        description=(
            "ForgePilot helps manufacturing teams automate quality workflows with AI."
        ),
    )


def _generic_snapshot(website_url: str) -> CompanySnapshot:
    return CompanySnapshot(
        company_name="Acme Analytics",
        industry="B2B SaaS",
        product="Self-serve analytics platform for startup teams",
        icp="Seed to Series B SaaS startups with 10-100 employees",
        pricing="$499/month Pro plan",
        stage="Seed",
        employees="12",
        funding="$2M seed round",
        website=website_url,
        description=(
            "Acme Analytics turns product data into actionable growth insights."
        ),
    )


def _supplemental_public_entries(snapshot: CompanySnapshot) -> list[tuple[str, str, str]]:
    is_forgepilot = "forgepilot" in snapshot.website.lower()
    headquarters = "Detroit, MI" if is_forgepilot else "Austin, TX"
    founded = "2021" if is_forgepilot else "2020"

    return [
        ("mission", "website", snapshot.website),
        ("company", "headquarters", headquarters),
        ("company", "founded", founded),
        ("product", "category", f"{snapshot.industry} software"),
        ("market", "problem", f"Teams in {snapshot.industry} need better visibility."),
        ("customer", "segment", snapshot.icp),
        ("sales", "motion", f"Go-to-market aligned to {snapshot.stage} stage"),
        ("team", "culture", f"{snapshot.employees} employees building {snapshot.product}"),
        (
            "vision",
            "mission",
            f"{snapshot.company_name} exists to improve {snapshot.industry.lower()}.",
        ),
        (
            "competitive",
            "positioning",
            f"{snapshot.company_name} differentiates through {snapshot.product.lower()}",
        ),
    ]


def _public_knowledge_entries(snapshot: CompanySnapshot) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []

    for field_name, domain, sub_domain in PUBLIC_SNAPSHOT_MAPPINGS:
        value = getattr(snapshot, field_name).strip()
        if value:
            entries.append((domain, sub_domain, value))

    entries.extend(_supplemental_public_entries(snapshot))
    return entries[:PUBLIC_KNOWLEDGE_OBJECT_COUNT]


def _private_knowledge_entries(
    private_knowledge: PrivateKnowledge,
) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []

    for field_name, domain, sub_domain, content_template in PRIVATE_KNOWLEDGE_MAPPINGS:
        raw_value = getattr(private_knowledge, field_name).strip()
        if not raw_value:
            continue

        content = content_template.format(value=raw_value)
        entries.append((domain, sub_domain, content))

    return entries


def _create_import_item(
    db: Session,
    *,
    domain: str,
    sub_domain: str,
    content: str,
    source_system: str,
    source_url: str,
    now: datetime,
) -> KnowledgeItem:
    item = KnowledgeItem(
        domain=domain,
        sub_domain=sub_domain,
        content=content,
        source_system=source_system,
        source_url=source_url,
        source_priority=IMPORT_SOURCE_PRIORITY,
        trust_rank=IMPORT_TRUST_RANK,
        allowed_roles=["founder", "admin", "member"],
        created_at=now,
        updated_at=now,
    )
    db.add(item)
    return item


def _recommended_next_steps(
    snapshot: CompanySnapshot,
    private_knowledge: PrivateKnowledge,
) -> list[str]:
    steps: list[str] = []

    if private_knowledge.founder_dependent_knowledge.strip():
        steps.append(
            "Document founder-dependent knowledge before scaling decision-making."
        )
    if private_knowledge.top_customer_objection.strip():
        steps.append("Organize customer objections by source, frequency, and date.")
    if snapshot.pricing.strip():
        steps.append("Capture pricing rationale and assign a source-of-truth owner.")
    if private_knowledge.current_mrr.strip() and private_knowledge.current_runway.strip():
        steps.append("Connect financial metrics to Stripe.")
    if snapshot.icp.strip():
        steps.append("Validate ICP against revenue and customer data.")

    return steps


def analyze_website(website_url: str) -> AnalyzeWebsiteResponse:
    if "forgepilot" in website_url.lower():
        snapshot = _forgepilot_snapshot(website_url)
    else:
        snapshot = _generic_snapshot(website_url)

    return AnalyzeWebsiteResponse(
        company_snapshot=snapshot,
        public_knowledge_objects=PUBLIC_KNOWLEDGE_OBJECT_COUNT,
        missing_private_fields=list(MISSING_PRIVATE_FIELDS),
    )


def generate_company_brain(
    db: Session, payload: GenerateBrainRequest
) -> GenerateBrainResponse:
    global _current_company_brain

    now = datetime.now(timezone.utc)
    snapshot = payload.company_snapshot
    private_knowledge = payload.private_knowledge
    website_url = snapshot.website

    db.execute(
        delete(KnowledgeItem).where(
            KnowledgeItem.source_system.in_([WEBSITE_IMPORT, FOUNDER_INPUT])
        )
    )
    db.flush()

    public_entries = _public_knowledge_entries(snapshot)
    private_entries = _private_knowledge_entries(private_knowledge)
    all_entries = [
        *(entry + (WEBSITE_IMPORT, website_url) for entry in public_entries),
        *(entry + (FOUNDER_INPUT, "") for entry in private_entries),
    ]

    slots = {(domain, sub_domain) for domain, sub_domain, _, _, _ in all_entries}
    for domain, sub_domain in slots:
        db.execute(
            delete(KnowledgeItem).where(
                KnowledgeItem.domain == domain,
                KnowledgeItem.sub_domain == sub_domain,
            )
        )
    db.flush()

    created_items: list[KnowledgeItem] = []

    for domain, sub_domain, content, source_system, source_url in all_entries:
        created_items.append(
            _create_import_item(
                db,
                domain=domain,
                sub_domain=sub_domain,
                content=content,
                source_system=source_system,
                source_url=source_url,
                now=now,
            )
        )

    db.commit()
    for item in created_items:
        db.refresh(item)

    domains_populated = sorted({item.domain for item in created_items})
    public_count = len(public_entries)
    founder_count = len(private_entries)

    _current_company_brain = {
        "company_name": snapshot.company_name,
        "domains_populated": domains_populated,
        "knowledge_count": len(created_items),
        "recommended_next_steps": _recommended_next_steps(snapshot, private_knowledge),
        "company_snapshot": snapshot.model_dump(),
        "private_knowledge": private_knowledge.model_dump(),
    }

    return GenerateBrainResponse(
        company_name=snapshot.company_name,
        public_knowledge_objects=public_count,
        founder_knowledge_objects=founder_count,
        total_knowledge_objects=len(created_items),
        items_created=[KnowledgeItemRead.model_validate(item) for item in created_items],
        company_brain_status="ready",
    )


def get_current_company_brain() -> CurrentBrainResponse:
    if _current_company_brain is None:
        return CurrentBrainResponse(
            company_name="",
            domains_populated=[],
            knowledge_count=0,
            recommended_next_steps=[],
        )

    return CurrentBrainResponse(
        company_name=_current_company_brain["company_name"],
        domains_populated=_current_company_brain["domains_populated"],
        knowledge_count=_current_company_brain["knowledge_count"],
        recommended_next_steps=_current_company_brain["recommended_next_steps"],
    )
