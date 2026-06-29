from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.schemas.authority_object import AuthorityObject
from app.schemas.company import (
    AnalyzeWebsiteResponse,
    CompanySnapshot,
    CurrentBrainResponse,
    ExtractionMetadata,
    GenerateBrainRequest,
    GenerateBrainResponse,
    PrivateKnowledge,
    PublicKnowledgeResponse,
)
from app.schemas.knowledge_item import KnowledgeItemRead
from app.services.authority_objects import (
    FOUNDER_INPUT_AUTHORITY,
    LEGACY_IMPORT_SOURCE_SYSTEMS,
    PUBLIC_KNOWLEDGE_OBJECT_COUNT,
    PUBLIC_WEBSITE_AUTHORITY,
    build_company_brain_authority_objects,
    build_public_authority_objects,
    build_supplemental_authority_objects,
    count_public_authority_objects,
    knowledge_item_from_authority_object,
)
from app.services.authority_score import build_authority_layer_summary
from app.services.website_extractor import (
    WebsiteEmptyError,
    WebsiteFetchError,
    extract_public_knowledge,
    normalize_website_url,
)

MISSING_PRIVATE_FIELDS = [
    "current_mrr",
    "current_runway",
    "top_customer_objection",
    "current_engineering_blocker",
    "founder_dependent_knowledge",
]

_current_company_brain: dict | None = None


def _extraction_metadata_from_extracted(extracted) -> ExtractionMetadata:
    return ExtractionMetadata(
        source_url=extracted.source_url,
        canonical_url=extracted.canonical_url,
        confidence=extracted.confidence,
        extraction_method="homepage_html",
        fields_extracted=extracted.fields_extracted,
        public_links=extracted.public_links,
    )


def _snapshot_from_extracted(extracted, normalized_url: str) -> CompanySnapshot:
    return CompanySnapshot(
        company_name=extracted.company_name,
        industry=extracted.industry,
        product=extracted.product,
        icp=extracted.icp,
        pricing=extracted.pricing,
        stage=extracted.stage,
        employees=extracted.employees,
        funding=extracted.funding,
        website=normalized_url,
        description=extracted.description,
    )


def _authority_objects_for_analysis(
    extracted,
    snapshot: CompanySnapshot,
    normalized_url: str,
) -> list[AuthorityObject]:
    authority_objects = build_public_authority_objects(extracted, normalized_url)
    authority_objects.extend(build_supplemental_authority_objects(snapshot))
    return authority_objects


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
    normalized_url = normalize_website_url(website_url)
    extracted = extract_public_knowledge(normalized_url)
    snapshot = _snapshot_from_extracted(extracted, normalized_url)
    authority_objects = _authority_objects_for_analysis(
        extracted, snapshot, normalized_url
    )

    return AnalyzeWebsiteResponse(
        company_snapshot=snapshot,
        public_knowledge_objects=PUBLIC_KNOWLEDGE_OBJECT_COUNT,
        missing_private_fields=list(MISSING_PRIVATE_FIELDS),
        extraction_metadata=_extraction_metadata_from_extracted(extracted),
        authority_objects=authority_objects,
        authority_layer_summary=build_authority_layer_summary(authority_objects),
    )


def get_public_knowledge(website_url: str) -> PublicKnowledgeResponse:
    normalized_url = normalize_website_url(website_url)
    extracted = extract_public_knowledge(normalized_url)
    authority_objects = build_public_authority_objects(extracted, normalized_url)

    return PublicKnowledgeResponse(
        website_url=normalized_url,
        company_name=extracted.company_name,
        authority_objects_count=len(authority_objects),
        authority_objects=authority_objects,
        extraction_metadata=_extraction_metadata_from_extracted(extracted),
        authority_layer_summary=build_authority_layer_summary(authority_objects),
    )


def generate_company_brain(
    db: Session, payload: GenerateBrainRequest
) -> GenerateBrainResponse:
    global _current_company_brain

    now = datetime.now(timezone.utc)
    snapshot = payload.company_snapshot
    private_knowledge = payload.private_knowledge

    authority_objects = build_company_brain_authority_objects(
        snapshot, private_knowledge
    )

    import_source_systems = (
        PUBLIC_WEBSITE_AUTHORITY,
        FOUNDER_INPUT_AUTHORITY,
        *LEGACY_IMPORT_SOURCE_SYSTEMS,
    )
    db.execute(
        delete(KnowledgeItem).where(
            KnowledgeItem.source_system.in_(import_source_systems)
        )
    )
    db.flush()

    slots = {(obj.domain, obj.sub_domain) for obj in authority_objects}
    for domain, sub_domain in slots:
        db.execute(
            delete(KnowledgeItem).where(
                KnowledgeItem.domain == domain,
                KnowledgeItem.sub_domain == sub_domain,
            )
        )
    db.flush()

    created_items: list[KnowledgeItem] = []
    for authority_object in authority_objects:
        item = knowledge_item_from_authority_object(authority_object, now)
        db.add(item)
        created_items.append(item)

    db.commit()
    for item in created_items:
        db.refresh(item)

    public_count = count_public_authority_objects(authority_objects)
    founder_count = sum(
        1 for obj in authority_objects if obj.authority == FOUNDER_INPUT_AUTHORITY
    )
    domains_populated = sorted({item.domain for item in created_items})

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
