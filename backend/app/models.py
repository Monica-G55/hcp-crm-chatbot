from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class HCP(Base):
    """A Healthcare Professional (doctor) that the field rep engages with."""
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    specialty = Column(String(150), nullable=True)
    hospital = Column(String(200), nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp")


class Interaction(Base):
    """A single logged interaction between a rep and an HCP."""
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)
    rep_name = Column(String(150), nullable=True)
    interaction_type = Column(String(50), default="visit")  # visit, call, email
    raw_input = Column(Text, nullable=True)          # original form/chat text
    summary = Column(Text, nullable=True)             # LLM generated summary
    products_discussed = Column(JSON, nullable=True)  # list extracted by LLM
    materials_shared = Column(JSON, nullable=True)
    sentiment = Column(String(30), nullable=True)      # positive/neutral/negative
    interaction_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")


class FollowUp(Base):
    """Scheduled follow-up tasks tied to an interaction."""
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False)
    due_date = Column(DateTime, nullable=False)
    note = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, done
    created_at = Column(DateTime, default=datetime.utcnow)
