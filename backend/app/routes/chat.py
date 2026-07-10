from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas
from ..agent.agent import run_agent

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    """Conversational entry point. The LangGraph agent classifies intent and
    routes to one of the 5 tools (log, edit, history, followup, summary)."""
    result = run_agent(db, payload.message, payload.rep_name)
    return schemas.ChatResponse(**result)
