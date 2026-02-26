from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Interaction(SQLModel, table=True):
    """
    A persisted record of one user request + one model response.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    input_text: str

    raw_model_output: Optional[str] = None
    parsed_json: Optional[str] = None

    status: str = "ok"  # "ok" or "error"
    error_message: Optional[str] = None


class LeadExtracted(SQLModel):
    """
    Response model for /api/extract.
    Not a table.
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    request_summary: Optional[str] = None
    urgency: Optional[str] = None  # "low" | "medium" | "high"


class InteractionOut(SQLModel):
    """
    Response schema for returning history items to the frontend.
    Not a table.
    """
    id: int
    created_at: datetime
    input_text: str
    status: str
    error_message: Optional[str] = None

    parsed_json: Optional[str] = None
    parsed: Optional[LeadExtracted] = None