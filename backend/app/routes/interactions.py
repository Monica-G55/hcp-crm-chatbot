from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..agent import tools

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("/")
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    """Structured form submission - still routed through the Log Interaction
    tool so the LLM can extract/clean up the summary and products."""
    text = f"HCP: {payload.hcp_name}. Notes: {payload.raw_input}"
    result = tools.log_interaction(db, text, payload.rep_name or "Field Rep")
    return result


@router.get("/")
def list_interactions(db: Session = Depends(get_db)):
    interactions = db.query(models.Interaction).order_by(models.Interaction.interaction_date.desc()).all()
    return [
        {
            "id": i.id,
            "hcp_id": i.hcp_id,
            "hcp_name": i.hcp.name if i.hcp else None,
            "rep_name": i.rep_name,
            "interaction_type": i.interaction_type,
            "summary": i.summary,
            "products_discussed": i.products_discussed,
            "sentiment": i.sentiment,
            "interaction_date": i.interaction_date,
        }
        for i in interactions
    ]


@router.put("/{interaction_id}")
def update_interaction(interaction_id: int, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    result = tools.edit_interaction(db, interaction_id, payload.dict(exclude_unset=True))
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/hcp/{hcp_name}/history")
def get_history(hcp_name: str, db: Session = Depends(get_db)):
    result = tools.fetch_hcp_history(db, hcp_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/{interaction_id}/followup")
def create_followup(interaction_id: int, days_from_now: int = 7, note: str = "", db: Session = Depends(get_db)):
    result = tools.schedule_followup(db, interaction_id, days_from_now, note)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/hcp/{hcp_name}/summary")
def get_summary(hcp_name: str, db: Session = Depends(get_db)):
    result = tools.generate_summary(db, hcp_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
