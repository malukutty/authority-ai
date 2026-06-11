from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine, get_db
from app.schemas.ask import AskRequest, AskResponse, SourceRead
from app.schemas.knowledge_item import KnowledgeItemCreate, KnowledgeItemRead
from app.schemas.seed import SeedResponse
from app.services.knowledge import (
    create_knowledge_item,
    list_knowledge_items,
    retrieve_knowledge,
    seed_knowledge_items,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Authority AI API", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "authority-ai-api"}


@app.post("/knowledge", response_model=KnowledgeItemRead, status_code=201)
def create_knowledge(payload: KnowledgeItemCreate, db: Session = Depends(get_db)):
    return create_knowledge_item(db, payload)


@app.get("/knowledge", response_model=list[KnowledgeItemRead])
def get_knowledge(db: Session = Depends(get_db)):
    return list_knowledge_items(db)


@app.post("/seed", response_model=SeedResponse)
def seed_knowledge(db: Session = Depends(get_db)):
    count_created, count_skipped = seed_knowledge_items(db)
    return SeedResponse(count_created=count_created, count_skipped=count_skipped)


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
