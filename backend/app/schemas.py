from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class InteractionCreate(BaseModel):
    hcp_name: str
    rep_name: Optional[str] = None
    interaction_type: Optional[str] = "visit"
    raw_input: str  # free text notes OR structured summary text from the form


class InteractionUpdate(BaseModel):
    summary: Optional[str] = None
    products_discussed: Optional[List[str]] = None
    sentiment: Optional[str] = None
    interaction_type: Optional[str] = None


class InteractionOut(BaseModel):
    id: int
    hcp_id: int
    rep_name: Optional[str]
    interaction_type: Optional[str]
    raw_input: Optional[str]
    summary: Optional[str]
    products_discussed: Optional[List[str]]
    sentiment: Optional[str]
    interaction_date: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    rep_name: Optional[str] = "Field Rep"


class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
    data: Optional[dict] = None
