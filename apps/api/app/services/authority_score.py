from datetime import datetime, timezone

from app.schemas.authority_object import AuthorityObject, AuthorityScoringBreakdown
from app.schemas.company import AuthorityLayerSummary, WeakestAuthorityObjectRead

AUTHORITY_SOURCE_SCORES: dict[str, int] = {
    "stripe": 100,
    "founder_input": 95,
    "public_website": 80,
}

SOURCE_TYPE_AUTHORITY_SCORES: dict[str, int] = {
    "homepage_meta_description": 80,
    "homepage_title": 75,
    "homepage_h1": 75,
    "homepage_text": 70,
    "heuristic_inference": 60,
    "detected_public_link": 65,
}

SUB_DOMAIN_AUTHORITY_SCORES: dict[str, int] = {
    "public_pricing_page": 90,
    "public_docs_page": 90,
    "public_about_page": 85,
}

EXTRACTION_CONFIDENCE_SCORES: dict[str, int] = {
    "high": 100,
    "medium": 70,
    "low": 30,
    "unknown": 20,
}

UNKNOWN_SOURCE_SCORE = 20
MAX_WEAKEST_OBJECTS = 5

GENERIC_VALUE_PHRASES = ("pricing page available",)


def _is_unknown_value(value: str) -> bool:
    return not value.strip() or value.strip() == "Unknown"


def _is_generic_value(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in GENERIC_VALUE_PHRASES or normalized.endswith(" page available")


def _is_url(value: str) -> bool:
    stripped = value.strip().lower()
    return stripped.startswith("http://") or stripped.startswith("https://")


def source_authority_score(authority_object: AuthorityObject) -> int:
    if authority_object.sub_domain in SUB_DOMAIN_AUTHORITY_SCORES:
        return SUB_DOMAIN_AUTHORITY_SCORES[authority_object.sub_domain]

    if authority_object.source_type in SOURCE_TYPE_AUTHORITY_SCORES:
        return SOURCE_TYPE_AUTHORITY_SCORES[authority_object.source_type]

    if authority_object.authority in AUTHORITY_SOURCE_SCORES:
        return AUTHORITY_SOURCE_SCORES[authority_object.authority]

    return UNKNOWN_SOURCE_SCORE


def extraction_confidence(authority_object: AuthorityObject) -> int:
    return EXTRACTION_CONFIDENCE_SCORES.get(
        authority_object.confidence.lower(),
        EXTRACTION_CONFIDENCE_SCORES["unknown"],
    )


def freshness_score(authority_object: AuthorityObject, now: datetime | None = None) -> int:
    extracted_at = authority_object.last_extracted_at
    if extracted_at is None:
        return 50

    reference = now or datetime.now(timezone.utc)
    if extracted_at.tzinfo is None:
        extracted_at = extracted_at.replace(tzinfo=timezone.utc)

    age_days = (reference - extracted_at).days
    if age_days < 7:
        return 100
    if age_days <= 30:
        return 80
    if age_days <= 90:
        return 60
    return 30


def completeness_score(authority_object: AuthorityObject) -> int:
    value = authority_object.value.strip()

    if _is_unknown_value(value):
        return 10

    if len(value) < 5:
        return 30

    if _is_generic_value(value):
        return 60

    if _is_url(value):
        return 70

    return 100


def consistency_score(authority_object: AuthorityObject) -> int:
    metadata = authority_object.metadata or {}

    if metadata.get("status") == "removed":
        return 20

    if metadata.get("conflict") is True:
        return 40

    return 100


def calculate_scoring_breakdown(
    authority_object: AuthorityObject,
    now: datetime | None = None,
) -> AuthorityScoringBreakdown:
    return AuthorityScoringBreakdown(
        source_authority_score=source_authority_score(authority_object),
        extraction_confidence=extraction_confidence(authority_object),
        freshness_score=freshness_score(authority_object, now=now),
        completeness_score=completeness_score(authority_object),
        consistency_score=consistency_score(authority_object),
    )


def composite_authority_score(breakdown: AuthorityScoringBreakdown) -> int:
    score = round(
        breakdown.source_authority_score * 0.40
        + breakdown.extraction_confidence * 0.20
        + breakdown.freshness_score * 0.15
        + breakdown.completeness_score * 0.15
        + breakdown.consistency_score * 0.10
    )
    return max(0, min(100, score))


def calculate_authority_score(
    authority_object: AuthorityObject,
    now: datetime | None = None,
) -> int:
    breakdown = calculate_scoring_breakdown(authority_object, now=now)
    return composite_authority_score(breakdown)


def weakness_reason(authority_object: AuthorityObject) -> str:
    breakdown = authority_object.scoring_breakdown or calculate_scoring_breakdown(
        authority_object
    )

    if breakdown.completeness_score <= 30:
        return "Missing or incomplete value"

    if breakdown.source_authority_score <= 60:
        return "Weak source authority"

    if breakdown.extraction_confidence <= 30:
        return "Low confidence"

    if breakdown.freshness_score <= 60:
        return "Stale knowledge"

    if breakdown.consistency_score <= 40:
        return "Consistency risk"

    return "Lower composite authority score"


def attach_authority_score(
    authority_object: AuthorityObject,
    now: datetime | None = None,
) -> AuthorityObject:
    breakdown = calculate_scoring_breakdown(authority_object, now=now)
    score = composite_authority_score(breakdown)
    return authority_object.model_copy(
        update={
            "authority_score": score,
            "scoring_breakdown": breakdown,
        }
    )


def build_authority_layer_summary(
    authority_objects: list[AuthorityObject],
) -> AuthorityLayerSummary:
    if not authority_objects:
        return AuthorityLayerSummary(
            average_authority_score=0,
            high_authority_objects=0,
            medium_authority_objects=0,
            low_authority_objects=0,
            weakest_objects=[],
        )

    scores = [obj.authority_score for obj in authority_objects]
    high_count = sum(1 for score in scores if score >= 85)
    medium_count = sum(1 for score in scores if 60 <= score <= 84)
    low_count = sum(1 for score in scores if score <= 59)

    weakest_candidates = sorted(
        authority_objects,
        key=lambda obj: (obj.authority_score, obj.domain, obj.sub_domain),
    )
    weakest_objects = [
        WeakestAuthorityObjectRead(
            domain=obj.domain,
            sub_domain=obj.sub_domain,
            value=obj.value,
            authority_score=obj.authority_score,
            reason=weakness_reason(obj),
        )
        for obj in weakest_candidates[:MAX_WEAKEST_OBJECTS]
        if obj.authority_score <= 84
    ]

    return AuthorityLayerSummary(
        average_authority_score=round(sum(scores) / len(scores), 1),
        high_authority_objects=high_count,
        medium_authority_objects=medium_count,
        low_authority_objects=low_count,
        weakest_objects=weakest_objects,
    )
