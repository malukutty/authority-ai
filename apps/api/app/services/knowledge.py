from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.schemas.ingest import NotionIngestRequest
from app.schemas.knowledge_item import KnowledgeItemCreate

RESTRICTED_DOMAINS = {
    "financial": ["founder", "admin"],
    "pipeline": ["founder", "admin"],
    "team": ["founder", "admin"],
}


def user_can_access_domain(domain: str, user_role: str) -> bool:
    allowed_roles = RESTRICTED_DOMAINS.get(domain)

    if allowed_roles is None:
        return True

    return user_role in allowed_roles


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


def ingest_notion(db: Session, payload: NotionIngestRequest) -> KnowledgeItem:
    domain, sub_domain, _knowledge_type = classify_content(payload.content)

    item_payload = KnowledgeItemCreate(
        domain=domain,
        sub_domain=sub_domain,
        content=payload.content,
        source_system="notion",
        source_url=payload.source_url,
        trust_rank=4,
    )
    return create_knowledge_item(db, item_payload)


def classify_question(question: str) -> tuple[list[str], list[str]]:
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
        return ["pipeline"], ["objection"]

    if "mrr" in q:
        return ["financial"], ["mrr"]
    if "arr" in q:
        return ["financial"], ["arr"]
    if "runway" in q:
        return ["financial"], ["runway"]
    if "burn" in q:
        return ["financial"], ["burn"]
    if "cash" in q:
        return ["financial"], ["cash"]

    engineering_keywords = ["blocker", "bug", "issue", "sprint", "deploy", "release"]
    if any(keyword in q for keyword in engineering_keywords):
        return ["engineering"], ["blocker"]

    if "icp" in q or "ideal customer" in q:
        return ["mission"], ["icp"]
    if any(keyword in q for keyword in ["product", "mission", "building"]):
        return ["mission"], ["product"]

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
        return ["decisions"], ["pricing"]
    if has_pricing:
        return ["decisions"], ["pricing"]
    if has_decision:
        return ["decisions"], []

    return [], []


SEED_ITEMS = [
    KnowledgeItemCreate(
        domain="financial",
        sub_domain="runway",
        content="Current runway is 14 months",
        source_system="manual_seed",
        trust_rank=1,
    ),
    KnowledgeItemCreate(
        domain="financial",
        sub_domain="mrr",
        content="Current MRR is $25000",
        source_system="manual_seed",
        trust_rank=1,
    ),
    KnowledgeItemCreate(
        domain="mission",
        sub_domain="icp",
        content="Ideal customer profile is YC-backed B2B SaaS startups with 5-50 employees",
        source_system="manual_seed",
        trust_rank=4,
    ),
    KnowledgeItemCreate(
        domain="mission",
        sub_domain="product",
        content="Authority AI is a schema-first company brain for startup teams",
        source_system="manual_seed",
        trust_rank=4,
    ),
    KnowledgeItemCreate(
        domain="pipeline",
        sub_domain="objection",
        content="Most common objection is security concerns around integrations",
        source_system="manual_seed",
        trust_rank=5,
    ),
    KnowledgeItemCreate(
        domain="engineering",
        sub_domain="blocker",
        content="Current blocker is Slack OAuth implementation",
        source_system="manual_seed",
        trust_rank=3,
    ),
]


def seed_knowledge_items(db: Session) -> tuple[int, int]:
    count_created = 0
    count_skipped = 0

    for payload in SEED_ITEMS:
        existing = db.scalar(
            select(KnowledgeItem).where(
                KnowledgeItem.domain == payload.domain,
                KnowledgeItem.sub_domain == payload.sub_domain,
                KnowledgeItem.content == payload.content,
            )
        )
        if existing:
            count_skipped += 1
            continue

        db.add(KnowledgeItem(**payload.model_dump()))
        count_created += 1

    db.commit()
    return count_created, count_skipped


def create_knowledge_item(db: Session, payload: KnowledgeItemCreate) -> KnowledgeItem:
    item = KnowledgeItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_knowledge_items(db: Session) -> list[KnowledgeItem]:
    return list(
        db.scalars(select(KnowledgeItem).order_by(KnowledgeItem.trust_rank)).all()
    )


def retrieve_knowledge(db: Session, question: str, user_role: str) -> list[KnowledgeItem]:
    domains, sub_domains = classify_question(question)

    allowed_domains = [
        domain for domain in domains if user_can_access_domain(domain, user_role)
    ]

    print(f"question: {question}")
    print(f"classified domains: {domains}")
    print(f"classified sub_domains: {sub_domains}")
    print(f"allowed_domains: {allowed_domains}")

    if not allowed_domains:
        print("number of items found: 0")
        return []

    if sub_domains:
        query = select(KnowledgeItem).where(
            KnowledgeItem.domain.in_(allowed_domains),
            KnowledgeItem.sub_domain.in_(sub_domains),
        )
    else:
        query = select(KnowledgeItem).where(
            KnowledgeItem.domain.in_(allowed_domains),
        )

    items = db.scalars(query).all()
    print(f"number of items found: {len(items)}")

    return sorted(items, key=lambda item: item.trust_rank)
