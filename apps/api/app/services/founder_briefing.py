from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.schemas.founder_briefing import DecisionScenarioRead, FounderBriefingResponse
from app.services.authority_resolution import resolve_current_truth
from app.services.brain import get_brain_health
from app.services.decision_recommendations import generate_decision_recommendations

SLOT_DISPLAY_NAMES: dict[tuple[str, str], str] = {
    ("decisions", "pricing"): "Pricing strategy",
    ("financial", "runway"): "Current runway",
    ("financial", "mrr"): "MRR",
    ("financial", "fundraising"): "Fundraising",
    ("pipeline", "objection"): "Customer objections",
    ("mission", "icp"): "Ideal customer profile",
    ("mission", "product"): "Product",
    ("engineering", "blocker"): "Engineering blockers",
    ("company", "stage"): "Company stage",
    ("company", "employees"): "Current headcount",
    ("company", "funding"): "Funding",
    ("team", "hiring"): "Hiring plan",
    ("product", "roadmap"): "Product roadmap",
    ("sales", "motion"): "Sales motion",
}

DECISION_SCENARIOS: list[DecisionScenarioRead] = [
    DecisionScenarioRead(
        title="Should we change pricing?",
        description="Review how a pricing change would affect revenue, objections, and ICP fit.",
        icon="dollar-sign",
    ),
    DecisionScenarioRead(
        title="Should we start fundraising?",
        description="Check whether runway, stage, and company profile support a fundraise.",
        icon="trending-up",
    ),
    DecisionScenarioRead(
        title="Should we hire another engineer?",
        description="Evaluate runway, hiring plans, and engineering capacity before expanding the team.",
        icon="users",
    ),
    DecisionScenarioRead(
        title="Should we expand sales?",
        description="Review ICP, objections, and sales motion before scaling go-to-market.",
        icon="target",
    ),
    DecisionScenarioRead(
        title="Should we enter enterprise?",
        description="Assess ICP, product readiness, and customer feedback for enterprise expansion.",
        icon="building",
    ),
    DecisionScenarioRead(
        title="What should I fix next?",
        description="See the highest-priority gaps reducing decision confidence in your Company Brain.",
        icon="wrench",
    ),
    DecisionScenarioRead(
        title="What does my Company Brain not know?",
        description="Review missing knowledge areas that weaken strategic and operational decisions.",
        icon="help-circle",
    ),
    DecisionScenarioRead(
        title="What could break this quarter?",
        description="Identify stale knowledge, conflicts, and coverage gaps that create business risk.",
        icon="alert-triangle",
    ),
]

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _display_name(domain: str, sub_domain: str) -> str:
    return SLOT_DISPLAY_NAMES.get(
        (domain, sub_domain),
        sub_domain.replace("_", " ").title(),
    )


def _count_active_knowledge(db: Session) -> int:
    return len(
        db.scalars(
            select(KnowledgeItem).where(KnowledgeItem.is_active.is_(True))
        ).all()
    )


def _build_summary(
    knowledge_count: int,
    resolved_count: int,
    missing_count: int,
    high_priority_gaps: int,
) -> str:
    parts = [
        f"Your Company Brain analyzed {knowledge_count} pieces of business knowledge."
    ]

    if resolved_count > 0:
        parts.append(
            "Most core business decisions are supported by authoritative internal knowledge."
        )
    else:
        parts.append(
            "Core business knowledge is still limited across important decision areas."
        )

    if missing_count > 0 or high_priority_gaps > 0:
        parts.append(
            "However, important gaps remain around company profile and decision coverage "
            "that reduce confidence for fundraising and strategic planning."
        )
    else:
        parts.append(
            "No major placeholder gaps were detected in the highest-priority decision areas."
        )

    return " ".join(parts)


def _resolved_observation(domain: str, sub_domain: str, chosen_source: str) -> str:
    label = _display_name(domain, sub_domain)
    if (domain, sub_domain) == ("decisions", "pricing"):
        return (
            f"{label} is documented in {chosen_source} and is considered authoritative."
        )
    if domain == "financial":
        return f"{label} is supported by {chosen_source}."
    return f"{label} is established through {chosen_source}."


def _missing_observation(domain: str, sub_domain: str) -> str:
    label = _display_name(domain, sub_domain)
    return f"Decision readiness is reduced because {label.lower()} is unknown."


def _build_top_observations(
    current_truth: list,
) -> list[str]:
    observations: list[str] = []

    resolved = [
        truth
        for truth in current_truth
        if truth.resolution_status == "resolved" and truth.chosen_source
    ]
    missing = [
        truth for truth in current_truth if truth.resolution_status == "missing_knowledge"
    ]
    conflict_review = [
        truth for truth in current_truth if truth.resolution_status == "conflict_review"
    ]

    priority_resolved = sorted(
        resolved,
        key=lambda truth: (
            0 if truth.domain in {"decisions", "financial"} else 1,
            -truth.resolution_confidence,
        ),
    )
    for truth in priority_resolved:
        observation = _resolved_observation(
            truth.domain,
            truth.sub_domain,
            truth.chosen_source or "",
        )
        if observation not in observations:
            observations.append(observation)
        if len(observations) >= 2:
            break

    for truth in sorted(
        missing,
        key=lambda item: (
            0 if item.domain == "company" else 1,
            item.sub_domain,
        ),
    ):
        observation = _missing_observation(truth.domain, truth.sub_domain)
        if observation not in observations:
            observations.append(observation)
        if len(observations) >= 3:
            break

    for truth in conflict_review:
        label = _display_name(truth.domain, truth.sub_domain)
        observation = (
            f"{label} has conflicting sources that should be reviewed before making "
            "related decisions."
        )
        if observation not in observations:
            observations.append(observation)
        if len(observations) >= 3:
            break

    return observations[:3]


def _build_business_risks(
    recommendations: list,
    current_truth: list,
    brain_health,
) -> list[str]:
    risks: list[str] = []

    for recommendation in sorted(
        recommendations,
        key=lambda item: PRIORITY_ORDER.get(item.priority, 99),
    ):
        if recommendation.reason not in risks:
            risks.append(recommendation.reason)
        if len(risks) >= 2:
            break

    missing_company = [
        truth
        for truth in current_truth
        if truth.resolution_status == "missing_knowledge" and truth.domain == "company"
    ]
    if missing_company:
        risks.append(
            "Fundraising decisions have low confidence because company profile "
            "knowledge is incomplete."
        )

    if brain_health.high_priority_stale:
        stale_name = brain_health.high_priority_stale[0].name
        risks.append(
            f"{stale_name} knowledge is stale and may no longer reflect current business reality."
        )

    for truth in current_truth:
        if truth.resolution_status != "conflict_review":
            continue
        label = _display_name(truth.domain, truth.sub_domain)
        risk = (
            f"{label} decisions may be unreliable until conflicting sources are reconciled."
        )
        if risk not in risks:
            risks.append(risk)
        break

    return risks[:3]


def _build_knowledge_gaps(
    current_truth: list,
    recommendations: list,
    brain_health,
) -> list[str]:
    gaps: list[str] = []

    for truth in current_truth:
        if truth.resolution_status != "missing_knowledge":
            continue
        label = _display_name(truth.domain, truth.sub_domain)
        if label not in gaps:
            gaps.append(label)
        if len(gaps) >= 3:
            return gaps

    for recommendation in sorted(
        recommendations,
        key=lambda item: PRIORITY_ORDER.get(item.priority, 99),
    ):
        gap = recommendation.title
        if gap not in gaps:
            gaps.append(gap)
        if len(gaps) >= 3:
            return gaps

    for entry in brain_health.high_priority_missing:
        if entry.name not in gaps:
            gaps.append(entry.name)
        if len(gaps) >= 3:
            break

    return gaps[:3]


def _build_recommended_actions(recommendations: list) -> list[str]:
    sorted_recommendations = sorted(
        recommendations,
        key=lambda item: PRIORITY_ORDER.get(item.priority, 99),
    )
    actions: list[str] = []
    for recommendation in sorted_recommendations:
        action = recommendation.recommended_action
        if action not in actions:
            actions.append(action)
        if len(actions) >= 3:
            break
    return actions


def generate_founder_briefing(db: Session) -> FounderBriefingResponse:
    current_truth = resolve_current_truth(db)
    decision_recommendations = generate_decision_recommendations(db).recommendations
    brain_health = get_brain_health(db)

    knowledge_count = _count_active_knowledge(db)
    resolved_count = sum(
        1 for truth in current_truth if truth.resolution_status == "resolved"
    )
    missing_count = sum(
        1 for truth in current_truth if truth.resolution_status == "missing_knowledge"
    )
    high_priority_gaps = sum(
        1
        for recommendation in decision_recommendations
        if recommendation.priority == "high"
    )

    return FounderBriefingResponse(
        summary=_build_summary(
            knowledge_count,
            resolved_count,
            missing_count,
            high_priority_gaps,
        ),
        top_observations=_build_top_observations(current_truth),
        business_risks=_build_business_risks(
            decision_recommendations,
            current_truth,
            brain_health,
        ),
        knowledge_gaps=_build_knowledge_gaps(
            current_truth,
            decision_recommendations,
            brain_health,
        ),
        recommended_actions=_build_recommended_actions(decision_recommendations),
        decision_scenarios=list(DECISION_SCENARIOS),
    )
