"""
The 5 tools available to the LangGraph HCP agent.

1. log_interaction      - captures + structures a new interaction using the LLM
2. edit_interaction      - modifies an already logged interaction
3. fetch_hcp_history     - retrieves an HCP's past interaction history
4. schedule_followup     - creates a follow-up reminder tied to an interaction
5. generate_summary      - produces an LLM-written summary report for an HCP
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import HCP, Interaction, FollowUp
from .llm import extract_interaction_details, summarize_history


def _get_or_create_hcp(db: Session, name: str) -> HCP:
    hcp = db.query(HCP).filter(HCP.name.ilike(name)).first()
    if not hcp:
        hcp = HCP(name=name)
        db.add(hcp)
        db.commit()
        db.refresh(hcp)
    return hcp


def log_interaction(db: Session, raw_text: str, rep_name: str = "Field Rep") -> dict:
    """Tool 1: Log Interaction.
    Uses the LLM to extract HCP name, summary, products discussed, and sentiment
    from free-form text (chat message or form notes), then saves it to the DB.
    """
    extracted = extract_interaction_details(raw_text)
    hcp = _get_or_create_hcp(db, extracted.get("hcp_name", "Unknown"))

    interaction = Interaction(
        hcp_id=hcp.id,
        rep_name=rep_name,
        interaction_type=extracted.get("interaction_type", "visit"),
        raw_input=raw_text,
        summary=extracted.get("summary"),
        products_discussed=extracted.get("products_discussed", []),
        materials_shared=extracted.get("materials_shared", []),
        sentiment=extracted.get("sentiment", "neutral"),
        interaction_date=datetime.utcnow(),
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    return {
        "interaction_id": interaction.id,
        "hcp_name": hcp.name,
        "summary": interaction.summary,
        "products_discussed": interaction.products_discussed,
        "materials_shared": interaction.materials_shared,
        "sentiment": interaction.sentiment,
    }


def edit_interaction(db: Session, interaction_id: int, updates: dict) -> dict:
    """Tool 2: Edit Interaction.
    Allows modification of a previously logged interaction's fields
    (summary, products discussed, sentiment, type).
    """
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        return {"error": f"Interaction {interaction_id} not found"}

    for field, value in updates.items():
        if value is not None and hasattr(interaction, field):
            setattr(interaction, field, value)

    interaction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(interaction)

    return {
        "interaction_id": interaction.id,
        "summary": interaction.summary,
        "products_discussed": interaction.products_discussed,
        "materials_shared": interaction.materials_shared,
        "sentiment": interaction.sentiment,
        "updated_at": str(interaction.updated_at),
    }


def fetch_hcp_history(db: Session, hcp_name: str) -> dict:
    """Tool 3: Fetch HCP History.
    Retrieves all past interactions logged for a given HCP.
    """
    hcp = db.query(HCP).filter(HCP.name.ilike(hcp_name)).first()
    if not hcp:
        return {"error": f"No HCP found with name {hcp_name}"}

    interactions = (
        db.query(Interaction)
        .filter(Interaction.hcp_id == hcp.id)
        .order_by(Interaction.interaction_date.desc())
        .all()
    )
    return {
        "hcp_name": hcp.name,
        "total_interactions": len(interactions),
        "interactions": [
            {
                "id": i.id,
                "date": str(i.interaction_date),
                "summary": i.summary,
                "products_discussed": i.products_discussed,
                "sentiment": i.sentiment,
            }
            for i in interactions
        ],
    }


def schedule_followup(db: Session, interaction_id: int, days_from_now: int = 7, note: str = "") -> dict:
    """Tool 4: Schedule Follow-up.
    Creates a follow-up reminder tied to a logged interaction, e.g. to revisit
    an HCP or send promised samples/literature.
    """
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        return {"error": f"Interaction {interaction_id} not found"}

    due_date = datetime.utcnow() + timedelta(days=days_from_now)
    followup = FollowUp(
        interaction_id=interaction_id,
        due_date=due_date,
        note=note or "Follow up on previous discussion",
    )
    db.add(followup)
    db.commit()
    db.refresh(followup)

    return {
        "followup_id": followup.id,
        "interaction_id": interaction_id,
        "due_date": str(followup.due_date),
        "note": followup.note,
    }


def generate_summary(db: Session, hcp_name: str) -> dict:
    """Tool 5: Generate Summary.
    Uses the LLM to produce a readable narrative report summarizing an HCP's
    engagement history - useful before a visit or for manager reporting.
    """
    history = fetch_hcp_history(db, hcp_name)
    if "error" in history:
        return history

    report = summarize_history(history["interactions"])
    return {
        "hcp_name": hcp_name,
        "report": report,
        "based_on_interactions": history["total_interactions"],
    }
