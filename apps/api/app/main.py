from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine, get_db
import app.models  # noqa: F401 — register models with Base.metadata
from app.schemas.ask import AskRequest, AskResponse, SourceRead
from app.schemas.ingest import NotionIngestRequest, StripeIngestRequest
from app.schemas.knowledge_item import KnowledgeItemCreate, KnowledgeItemRead
from app.schemas.knowledge_relationship import (
    KnowledgeItemRelationshipsResponse,
    KnowledgeRelationshipCreate,
    KnowledgeRelationshipRead,
)
from app.schemas.seed import ResetDemoResponse, SeedResponse
from app.services.demo import reset_demo
from app.services.knowledge import (
    create_knowledge_item,
    ingest_notion,
    ingest_stripe,
    list_knowledge_items,
    retrieve_knowledge,
    seed_knowledge_items,
)
from app.services.relationship import (
    create_knowledge_relationship,
    get_knowledge_relationships,
    seed_knowledge_relationships,
)
from app.services.source_priority import ensure_source_priority_column


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_source_priority_column()
    yield


app = FastAPI(title="Authority AI API", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "authority-ai-api"}


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
