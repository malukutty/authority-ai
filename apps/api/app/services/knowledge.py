from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.schemas.ingest import NotionIngestRequest, StripeIngestRequest
from app.schemas.knowledge_item import KnowledgeItemCreate
from app.services.source_priority import get_source_priority


def user_can_access_item(item: KnowledgeItem, user_role: str) -> bool:
    return user_role in item.allowed_roles


def classify_content(content: str) -> tuple[str, str, str]:
    text = content.lower()

    pricing_keywords = ["pricing", "price", "plan", "package"]
    if any(keyword in text for keyword in pricing_keywords):
        return "decisions", "pricing", "decision"

    icp_keywords = ["icp", "ideal customer", "target customer"]
    if any(keyword in text for keyword in icp_keywords):
        return "mission", "icp", "definition"

    if "mrr" in text:
        return "financial", "mrr", "metric"
    if "arr" in text:
        return "financial", "arr", "metric"
    if "runway" in text:
        return "financial", "runway", "metric"
    if "burn" in text:
        return "financial", "burn", "metric"
    if "cash" in text:
        return "financial", "cash", "metric"

    engineering_keywords = ["blocker", "bug", "issue", "sprint"]
    if any(keyword in text for keyword in engineering_keywords):
        return "engineering", "blocker", "blocker"

    return "decisions", "general", "note"


def ingest_stripe(db: Session, payload: StripeIngestRequest) -> KnowledgeItem:
    metric_label = payload.metric.upper()
    item_payload = KnowledgeItemCreate(
        domain="financial",
        sub_domain=payload.metric.lower(),
        content=f"Current {metric_label} is {payload.value}",
        source_system="stripe",
        trust_rank=1,
        allowed_roles=payload.allowed_roles,
    )
    return create_knowledge_item(db, item_payload)


def ingest_notion(db: Session, payload: NotionIngestRequest) -> KnowledgeItem:
    domain, sub_domain, _knowledge_type = classify_content(payload.content)

    item_payload = KnowledgeItemCreate(
        domain=domain,
        sub_domain=sub_domain,
        content=payload.content,
        source_system="notion",
        source_url=payload.source_url,
        trust_rank=4,
        allowed_roles=payload.allowed_roles,
    )
    return create_knowledge_item(db, item_payload)


def classify_question(question: str) -> list[tuple[str, str | None]]:
    q = question.lower()

    objection_keywords = [
        "worried",
        "concern",
        "concerns",
        "objection",
        "objections",
        "afraid",
        "hesitant",
    ]
    if "blocker to buying" in q or any(keyword in q for keyword in objection_keywords):
        return [("pipeline", "objection")]

    if "mrr" in q:
        return [("financial", "mrr")]
    if "arr" in q:
        return [("financial", "arr")]
    if "runway" in q:
        return [("financial", "runway")]
    if "burn" in q:
        return [("financial", "burn")]
    if "cash" in q:
        return [("financial", "cash")]

    engineering_keywords = ["blocker", "bug", "issue", "sprint", "deploy", "release"]
    if any(keyword in q for keyword in engineering_keywords):
        return [("engineering", "blocker")]

    if "icp" in q or "ideal customer" in q:
        return [("mission", "icp")]

    pricing_keywords = ["pricing", "price", "plan", "package", "charge", "cost"]
    decision_keywords = [
        "decided",
        "decide",
        "decision",
        "choose",
        "chose",
        "agreed",
        "rationale",
        "why did",
    ]

    has_pricing = any(keyword in q for keyword in pricing_keywords)
    has_decision = any(keyword in q for keyword in decision_keywords)

    if has_pricing and has_decision:
        return [("decisions", "pricing")]
    if has_pricing:
        return [("decisions", "pricing")]
    if has_decision:
        return [("decisions", None)]

    if any(
        phrase in q
        for phrase in ["description", "company description", "describe the company"]
    ):
        return [("mission", "description"), ("mission", "product")]

    if any(
        phrase in q
        for phrase in [
            "what does the company do",
            "what do we do",
            "what does this company do",
            "what is the product",
        ]
    ) or "product" in q:
        return [("mission", "product"), ("mission", "description")]

    if any(phrase in q for phrase in ["stage", "what stage", "company stage"]):
        return [("company", "stage")]

    if any(
        phrase in q for phrase in ["employees", "team size", "how many employees"]
    ):
        return [("company", "employees")]

    if any(phrase in q for phrase in ["funding", "funded", "funding round"]):
        return [("company", "funding")]

    if any(phrase in q for phrase in ["company name", "who are we", "name"]):
        return [("mission", "company")]

    if any(phrase in q for phrase in ["industry", "category", "market"]):
        return [("mission", "industry"), ("product", "category")]

    if any(phrase in q for phrase in ["website", "url"]):
        return [("mission", "website")]

    return []


SEED_ITEMS = [
    KnowledgeItemCreate(
        domain="financial",
        sub_domain="mrr",
        content="Current MRR is $25000",
        source_system="stripe",
        trust_rank=1,
        allowed_roles=["founder", "finance"],
    ),
    KnowledgeItemCreate(
        domain="financial",
        sub_domain="runway",
        content="Current runway is 14 months",
        source_system="notion",
        trust_rank=1,
        allowed_roles=["founder", "finance"],
    ),
    KnowledgeItemCreate(
        domain="decisions",
        sub_domain="pricing",
        content="We decided to price Authority AI at $500/month for seed-stage startups.",
        source_system="notion",
        source_url="https://notion.so/example",
        trust_rank=4,
        allowed_roles=["founder", "sales"],
    ),
    KnowledgeItemCreate(
        domain="mission",
        sub_domain="icp",
        content="Ideal customer profile is YC-backed B2B SaaS startups with 5-50 employees",
        source_system="manual_seed",
        trust_rank=4,
        allowed_roles=["founder", "member"],
    ),
    KnowledgeItemCreate(
        domain="mission",
        sub_domain="product",
        content="Authority AI is a schema-first company brain for startup teams",
        source_system="manual_seed",
        trust_rank=4,
        allowed_roles=["founder", "member"],
    ),
    KnowledgeItemCreate(
        domain="engineering",
        sub_domain="blocker",
        content="Current blocker is Slack OAuth implementation",
        source_system="manual_seed",
        trust_rank=3,
        allowed_roles=["founder", "engineering"],
    ),
]


def _find_seed_item(db: Session, payload: KnowledgeItemCreate) -> KnowledgeItem | None:
    return db.scalar(
        select(KnowledgeItem).where(
            KnowledgeItem.domain == payload.domain,
            KnowledgeItem.sub_domain == payload.sub_domain,
            KnowledgeItem.content == payload.content,
        )
    )


def sync_seed_allowed_roles() -> int:
    from app.db.session import SessionLocal

    updated = 0
    with SessionLocal() as db:
        for payload in SEED_ITEMS:
            existing = _find_seed_item(db, payload)
            if existing is None:
                continue

            desired_roles = list(payload.allowed_roles)
            current_roles = list(existing.allowed_roles)
            if current_roles != desired_roles:
                existing.allowed_roles = desired_roles
                updated += 1

        if updated:
            db.commit()

    return updated


def seed_knowledge_items(db: Session) -> tuple[int, int]:
    count_created = 0
    count_skipped = 0

    for payload in SEED_ITEMS:
        existing = _find_seed_item(db, payload)
        if existing:
            desired_roles = list(payload.allowed_roles)
            if list(existing.allowed_roles) != desired_roles:
                existing.allowed_roles = desired_roles
            count_skipped += 1
            continue

        item_data = payload.model_dump()
        item_data["source_priority"] = get_source_priority(payload.source_system)
        db.add(KnowledgeItem(**item_data))
        count_created += 1

    db.commit()
    return count_created, count_skipped


def create_knowledge_item(db: Session, payload: KnowledgeItemCreate) -> KnowledgeItem:
    item_data = payload.model_dump()
    if item_data["source_priority"] is None:
        item_data["source_priority"] = get_source_priority(payload.source_system)

    item = KnowledgeItem(**item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_knowledge_item(db: Session, knowledge_id: int) -> None:
    item = db.get(KnowledgeItem, knowledge_id)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail=f"KnowledgeItem with id {knowledge_id} not found",
        )

    db.delete(item)
    db.commit()


def list_knowledge_items(db: Session) -> list[KnowledgeItem]:
    return list(
        db.scalars(
            select(KnowledgeItem).order_by(
                KnowledgeItem.source_priority,
                KnowledgeItem.trust_rank,
            )
        ).all()
    )


def retrieve_knowledge(db: Session, question: str, user_role: str) -> list[KnowledgeItem]:
    slots = classify_question(question)

    print(f"question: {question}")
    print(f"classified slots: {slots}")
    print(f"user_role: {user_role}")

    if not slots:
        print("number of items found: 0")
        return []

    for domain, sub_domain in slots:
        if sub_domain is None:
            query = select(KnowledgeItem).where(KnowledgeItem.domain == domain)
        else:
            query = select(KnowledgeItem).where(
                KnowledgeItem.domain == domain,
                KnowledgeItem.sub_domain == sub_domain,
            )

        items = db.scalars(query).all()
        permitted_items = [
            item for item in items if user_can_access_item(item, user_role)
        ]
        if permitted_items:
            print(f"number of items found: {len(permitted_items)}")
            return sorted(
                permitted_items,
                key=lambda item: (item.source_priority, item.trust_rank),
            )

    print("number of items found: 0")
    return []
