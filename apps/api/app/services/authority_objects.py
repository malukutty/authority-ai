from datetime import datetime, timezone

from typing import Literal, TypedDict

from app.models.knowledge_item import KnowledgeItem
from app.schemas.authority_object import AuthorityObject
from app.schemas.company import CompanySnapshot, PrivateKnowledge
from app.services.website_extractor import ExtractedWebsiteData

PUBLIC_WEBSITE_AUTHORITY = "public_website"
FOUNDER_INPUT_AUTHORITY = "founder_input"
EXTRACTION_METHOD_HOMEPAGE = "homepage_html"
EXTRACTION_METHOD_MANUAL = "manual_input"

IMPORT_SOURCE_PRIORITY = 10
IMPORT_TRUST_RANK = 3
PUBLIC_KNOWLEDGE_OBJECT_COUNT = 19

PUBLIC_FIELD_MAPPINGS: list[tuple[str, str, str, str]] = [
    ("company_name", "mission", "company", "homepage_title"),
    ("industry", "mission", "industry", "heuristic_inference"),
    ("product", "mission", "product", "homepage_h1"),
    ("description", "mission", "description", "homepage_meta_description"),
    ("icp", "mission", "icp", "heuristic_inference"),
    ("pricing", "decisions", "pricing", "heuristic_inference"),
    ("stage", "company", "stage", "heuristic_inference"),
    ("employees", "company", "employees", "heuristic_inference"),
    ("funding", "company", "funding", "heuristic_inference"),
]

PUBLIC_LINK_MAPPINGS: dict[str, str] = {
    "pricing": "public_pricing_page",
    "docs": "public_docs_page",
    "careers": "public_careers_page",
    "about": "public_about_page",
    "contact": "public_contact_page",
    "blog": "public_blog_page",
}

PRIVATE_FIELD_MAPPINGS: list[tuple[str, str, str, str]] = [
    ("current_mrr", "financial", "mrr", "Current MRR is {value}"),
    ("current_runway", "financial", "runway", "Current runway is {value}"),
    ("top_customer_objection", "pipeline", "objection", "{value}"),
    ("current_engineering_blocker", "engineering", "blocker", "{value}"),
    (
        "founder_dependent_knowledge",
        "operations",
        "founder_dependency",
        "{value}",
    ),
]

LEGACY_IMPORT_SOURCE_SYSTEMS = ("website_import", "founder_input")
PUBLIC_SOURCE_SYSTEMS = (PUBLIC_WEBSITE_AUTHORITY, "website_import")


class AuthorityObjectDiff(TypedDict):
    new: list[AuthorityObject]
    updated: list[tuple[AuthorityObject, AuthorityObject]]
    removed: list[AuthorityObject]
    unchanged: list[AuthorityObject]


def _authority_object_id(domain: str, sub_domain: str) -> str:
    return f"{domain}/{sub_domain}"


def _field_confidence(
    value: str,
    field_name: str,
    fields_extracted: list[str],
    overall_confidence: str,
) -> str:
    if not value.strip() or value.strip() == "Unknown":
        return "low"
    if field_name in fields_extracted:
        return overall_confidence
    if overall_confidence == "high":
        return "medium"
    return overall_confidence


def _make_authority_object(
    *,
    domain: str,
    sub_domain: str,
    value: str,
    source_type: str,
    source_url: str,
    authority: str,
    confidence: str,
    extraction_method: str,
    last_extracted_at: datetime,
    metadata: dict | None = None,
) -> AuthorityObject | None:
    if not value.strip():
        return None

    return AuthorityObject(
        id=_authority_object_id(domain, sub_domain),
        domain=domain,
        sub_domain=sub_domain,
        value=value.strip(),
        source_type=source_type,
        source_url=source_url,
        authority=authority,
        confidence=confidence,
        extraction_method=extraction_method,
        last_extracted_at=last_extracted_at,
        metadata=metadata or {},
    )


def build_public_authority_objects(
    extraction_result: ExtractedWebsiteData,
    website_url: str,
) -> list[AuthorityObject]:
    now = datetime.now(timezone.utc)
    overall_confidence = extraction_result.confidence
    source_url = extraction_result.source_url
    objects: list[AuthorityObject] = []

    for field_name, domain, sub_domain, source_type in PUBLIC_FIELD_MAPPINGS:
        value = getattr(extraction_result, field_name, "")
        obj = _make_authority_object(
            domain=domain,
            sub_domain=sub_domain,
            value=value,
            source_type=source_type,
            source_url=source_url,
            authority=PUBLIC_WEBSITE_AUTHORITY,
            confidence=_field_confidence(
                value,
                field_name,
                extraction_result.fields_extracted,
                overall_confidence,
            ),
            extraction_method=EXTRACTION_METHOD_HOMEPAGE,
            last_extracted_at=now,
            metadata={"field": field_name},
        )
        if obj is not None:
            objects.append(obj)

    website_obj = _make_authority_object(
        domain="mission",
        sub_domain="website",
        value=website_url,
        source_type="detected_public_link",
        source_url=source_url,
        authority=PUBLIC_WEBSITE_AUTHORITY,
        confidence=overall_confidence,
        extraction_method=EXTRACTION_METHOD_HOMEPAGE,
        last_extracted_at=now,
        metadata={"field": "website"},
    )
    if website_obj is not None:
        objects.append(website_obj)

    for link_key, sub_domain in PUBLIC_LINK_MAPPINGS.items():
        link_url = extraction_result.public_links.get(link_key)
        if not link_url:
            continue

        obj = _make_authority_object(
            domain="source",
            sub_domain=sub_domain,
            value=link_url,
            source_type="detected_public_link",
            source_url=link_url,
            authority=PUBLIC_WEBSITE_AUTHORITY,
            confidence=overall_confidence,
            extraction_method=EXTRACTION_METHOD_HOMEPAGE,
            last_extracted_at=now,
            metadata={"link_type": link_key},
        )
        if obj is not None:
            objects.append(obj)

    return objects


def compare_authority_objects(
    old_authority_objects: list[AuthorityObject],
    new_authority_objects: list[AuthorityObject],
) -> AuthorityObjectDiff:
    old_map = {
        (obj.domain, obj.sub_domain): obj for obj in old_authority_objects
    }
    new_map = {
        (obj.domain, obj.sub_domain): obj for obj in new_authority_objects
    }

    diff: AuthorityObjectDiff = {
        "new": [],
        "updated": [],
        "removed": [],
        "unchanged": [],
    }

    for key, new_obj in new_map.items():
        old_obj = old_map.get(key)
        if old_obj is None:
            diff["new"].append(new_obj)
        elif old_obj.value == new_obj.value:
            diff["unchanged"].append(new_obj)
        else:
            diff["updated"].append((old_obj, new_obj))

    for key, old_obj in old_map.items():
        if key not in new_map:
            diff["removed"].append(old_obj)

    return diff


def authority_object_from_knowledge_item(item: KnowledgeItem) -> AuthorityObject:
    return AuthorityObject(
        id=_authority_object_id(item.domain, item.sub_domain),
        domain=item.domain,
        sub_domain=item.sub_domain,
        value=item.content,
        source_type="stored_knowledge_item",
        source_url=item.source_url,
        authority=item.source_system,
        confidence="medium",
        extraction_method=EXTRACTION_METHOD_HOMEPAGE,
        last_extracted_at=item.updated_at,
        metadata={"is_active": item.is_active},
    )


def build_snapshot_authority_objects(snapshot: CompanySnapshot) -> list[AuthorityObject]:
    now = datetime.now(timezone.utc)
    objects: list[AuthorityObject] = []

    for field_name, domain, sub_domain, source_type in PUBLIC_FIELD_MAPPINGS:
        value = getattr(snapshot, field_name, "")
        obj = _make_authority_object(
            domain=domain,
            sub_domain=sub_domain,
            value=value,
            source_type=source_type,
            source_url=snapshot.website,
            authority=PUBLIC_WEBSITE_AUTHORITY,
            confidence="low" if value.strip() == "Unknown" else "medium",
            extraction_method=EXTRACTION_METHOD_HOMEPAGE,
            last_extracted_at=now,
            metadata={"field": field_name},
        )
        if obj is not None:
            objects.append(obj)

    website_obj = _make_authority_object(
        domain="mission",
        sub_domain="website",
        value=snapshot.website,
        source_type="detected_public_link",
        source_url=snapshot.website,
        authority=PUBLIC_WEBSITE_AUTHORITY,
        confidence="medium",
        extraction_method=EXTRACTION_METHOD_HOMEPAGE,
        last_extracted_at=now,
        metadata={"field": "website"},
    )
    if website_obj is not None:
        objects.append(website_obj)

    return objects


def build_supplemental_authority_objects(
    snapshot: CompanySnapshot,
) -> list[AuthorityObject]:
    now = datetime.now(timezone.utc)
    supplemental_values: list[tuple[str, str, str]] = [
        ("company", "headquarters", "Unknown"),
        ("company", "founded", "Unknown"),
        ("product", "category", f"{snapshot.industry} software"),
        ("market", "problem", f"Teams in {snapshot.industry} need better visibility."),
        ("customer", "segment", snapshot.icp),
        ("sales", "motion", f"Go-to-market aligned to {snapshot.stage} stage"),
        (
            "team",
            "culture",
            f"{snapshot.employees} employees building {snapshot.product}",
        ),
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

    objects: list[AuthorityObject] = []
    for domain, sub_domain, value in supplemental_values:
        obj = _make_authority_object(
            domain=domain,
            sub_domain=sub_domain,
            value=value,
            source_type="heuristic_inference",
            source_url=snapshot.website,
            authority=PUBLIC_WEBSITE_AUTHORITY,
            confidence="low" if value.strip() == "Unknown" else "medium",
            extraction_method=EXTRACTION_METHOD_HOMEPAGE,
            last_extracted_at=now,
            metadata={"supplemental": True},
        )
        if obj is not None:
            objects.append(obj)

    return objects


def build_private_authority_objects(
    private_knowledge: PrivateKnowledge,
) -> list[AuthorityObject]:
    now = datetime.now(timezone.utc)
    objects: list[AuthorityObject] = []

    for field_name, domain, sub_domain, content_template in PRIVATE_FIELD_MAPPINGS:
        raw_value = getattr(private_knowledge, field_name, "").strip()
        if not raw_value:
            continue

        obj = _make_authority_object(
            domain=domain,
            sub_domain=sub_domain,
            value=content_template.format(value=raw_value),
            source_type="founder_private_knowledge",
            source_url="",
            authority=FOUNDER_INPUT_AUTHORITY,
            confidence="medium",
            extraction_method=EXTRACTION_METHOD_MANUAL,
            last_extracted_at=now,
            metadata={"field": field_name},
        )
        if obj is not None:
            objects.append(obj)

    return objects


def build_company_brain_authority_objects(
    snapshot: CompanySnapshot,
    private_knowledge: PrivateKnowledge,
) -> list[AuthorityObject]:
    public_objects = build_snapshot_authority_objects(snapshot)
    public_objects.extend(build_supplemental_authority_objects(snapshot))
    public_objects = public_objects[:PUBLIC_KNOWLEDGE_OBJECT_COUNT]

    private_objects = build_private_authority_objects(private_knowledge)
    return public_objects + private_objects


def count_public_authority_objects(objects: list[AuthorityObject]) -> int:
    return sum(1 for obj in objects if obj.authority == PUBLIC_WEBSITE_AUTHORITY)


def knowledge_item_from_authority_object(
    authority_object: AuthorityObject,
    now: datetime,
) -> KnowledgeItem:
    return KnowledgeItem(
        domain=authority_object.domain,
        sub_domain=authority_object.sub_domain,
        content=authority_object.value,
        source_system=authority_object.authority,
        source_url=authority_object.source_url,
        source_priority=IMPORT_SOURCE_PRIORITY,
        trust_rank=IMPORT_TRUST_RANK,
        allowed_roles=["founder", "admin", "member"],
        created_at=now,
        updated_at=now,
        is_active=True,
    )
