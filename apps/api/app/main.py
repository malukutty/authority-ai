from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine, get_db
import app.models  # noqa: F401 — register models with Base.metadata
from app.schemas.ask import AskRequest, AskResponse, SourceRead
from app.schemas.brain import (
    BrainCoverageResponse,
    BrainFreshnessResponse,
    BrainHealthResponse,
    BrainRecommendationsResponse,
    BrainSubDomainRead,
)
from app.schemas.ingest import NotionIngestRequest, StripeIngestRequest
from app.schemas.knowledge_item import KnowledgeItemCreate, KnowledgeItemRead
from app.schemas.knowledge_relationship import (
    BrainRelationshipsResponse,
    KnowledgeImpactResponse,
    KnowledgeItemRelationshipsResponse,
    KnowledgeRelationshipCreate,
    KnowledgeRelationshipRead,
)
from app.schemas.seed import CleanDemoResponse, ResetDemoResponse, SeedResponse
from app.services.brain import (
    get_brain_coverage,
    get_brain_freshness,
    get_brain_health,
    get_brain_recommendations,
    get_brain_structure,
    initialize_brain,
    sync_definition_importance_scores,
)
from app.services.demo import reset_demo, seed_clean_demo, seed_freshness_test
from app.services.knowledge import (
    create_knowledge_item,
    delete_knowledge_item,
    ingest_notion,
    ingest_stripe,
    list_knowledge_items,
    retrieve_knowledge,
    seed_knowledge_items,
    sync_seed_allowed_roles,
)
from app.services.relationship import (
    create_knowledge_relationship,
    get_brain_relationships,
    get_knowledge_impact,
    get_knowledge_relationships,
    seed_knowledge_relationships,
)
from app.services.source_priority import (
    ensure_allowed_roles_column,
    ensure_importance_score_column,
    ensure_source_priority_column,
    ensure_timestamp_columns,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_source_priority_column()
    ensure_allowed_roles_column()
    ensure_timestamp_columns()
    ensure_importance_score_column()
    sync_seed_allowed_roles()
    initialize_brain()
    sync_definition_importance_scores()
    yield


app = FastAPI(title="Authority AI API", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "authority-ai-api"}


@app.get("/brain", response_model=dict[str, list[BrainSubDomainRead]])
def get_brain(db: Session = Depends(get_db)):
    return get_brain_structure(db)


@app.get("/brain/coverage", response_model=BrainCoverageResponse)
def get_brain_coverage_endpoint(db: Session = Depends(get_db)):
    return get_brain_coverage(db)


@app.get("/brain/recommendations", response_model=BrainRecommendationsResponse)
def get_brain_recommendations_endpoint(db: Session = Depends(get_db)):
    return get_brain_recommendations(db)


@app.get("/brain/freshness", response_model=BrainFreshnessResponse)
def get_brain_freshness_endpoint(db: Session = Depends(get_db)):
    return get_brain_freshness(db)


@app.get("/brain/health", response_model=BrainHealthResponse)
def get_brain_health_endpoint(db: Session = Depends(get_db)):
    return get_brain_health(db)


@app.get("/brain/relationships", response_model=BrainRelationshipsResponse)
def get_brain_relationships_endpoint(db: Session = Depends(get_db)):
    return get_brain_relationships(db)


@app.get("/impact", response_model=KnowledgeImpactResponse)
def get_impact(
    domain: str,
    sub_domain: str,
    db: Session = Depends(get_db),
):
    return get_knowledge_impact(db, domain, sub_domain)


@app.post("/ingest/notion", response_model=KnowledgeItemRead, status_code=201)
def ingest_notion_content(payload: NotionIngestRequest, db: Session = Depends(get_db)):
    return ingest_notion(db, payload)


@app.post("/ingest/stripe", response_model=KnowledgeItemRead, status_code=201)
def ingest_stripe_content(payload: StripeIngestRequest, db: Session = Depends(get_db)):
    return ingest_stripe(db, payload)


@app.post("/knowledge", response_model=KnowledgeItemRead, status_code=201)
def create_knowledge(payload: KnowledgeItemCreate, db: Session = Depends(get_db)):
    return create_knowledge_item(db, payload)


@app.post("/relationship", response_model=KnowledgeRelationshipRead, status_code=201)
def create_relationship(
    payload: KnowledgeRelationshipCreate, db: Session = Depends(get_db)
):
    return create_knowledge_relationship(db, payload)


@app.get("/knowledge", response_model=list[KnowledgeItemRead])
def get_knowledge(db: Session = Depends(get_db)):
    return list_knowledge_items(db)


@app.delete("/knowledge/{knowledge_id}", status_code=204)
def delete_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    delete_knowledge_item(db, knowledge_id)


@app.get("/knowledge/{knowledge_id}/relationships", response_model=KnowledgeItemRelationshipsResponse)
def get_knowledge_item_relationships(
    knowledge_id: int, db: Session = Depends(get_db)
):
    item, relationships = get_knowledge_relationships(db, knowledge_id)
    return KnowledgeItemRelationshipsResponse(
        knowledge_item=item,
        relationships=relationships,
    )


@app.post("/seed", response_model=SeedResponse)
def seed_knowledge(db: Session = Depends(get_db)):
    count_created, count_skipped = seed_knowledge_items(db)
    relationships_created, relationships_skipped = seed_knowledge_relationships(db)
    return SeedResponse(
        count_created=count_created,
        count_skipped=count_skipped,
        relationships_created=relationships_created,
        relationships_skipped=relationships_skipped,
    )


@app.post("/seed/freshness-test", response_model=list[KnowledgeItemRead])
def seed_freshness_test_data(db: Session = Depends(get_db)):
    return seed_freshness_test(db)


@app.post("/seed/clean-demo", response_model=CleanDemoResponse)
def seed_clean_demo_data(db: Session = Depends(get_db)):
    return seed_clean_demo(db)


@app.delete("/reset-demo", response_model=ResetDemoResponse)
def reset_demo_data(db: Session = Depends(get_db)):
    return reset_demo(db)


@app.post("/ask", response_model=AskResponse)
def ask_authority(request: AskRequest, db: Session = Depends(get_db)):
    items = retrieve_knowledge(db, request.question, request.user_role)

    if not items:
        return AskResponse(
            question=request.question,
            answer="I don't have enough permitted knowledge to answer that.",
            confidence="low",
            sources=[],
            user_role=request.user_role,
        )

    top_item = items[0]

    return AskResponse(
        question=request.question,
        answer=top_item.content,
        confidence="medium",
        sources=[
            SourceRead(
                source_system=top_item.source_system,
                source_url=top_item.source_url,
                trust_rank=top_item.trust_rank,
            )
        ],
        user_role=request.user_role,
    )
