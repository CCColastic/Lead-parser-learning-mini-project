from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Interaction(SQLModel, table=True):
    """
    A persisted record of one user request + one model response.

    table=True tells SQLModel this class becomes a real database table, \
    Get Registred with metadata.create_all() to create the table in the database.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    input_text: str

    # We'll store model outputs later. For now keep nullable so DB can exist.
    raw_model_output: Optional[str] = None
    parsed_json: Optional[str] = None

    status: str = "ok"  # "ok" or "error"
    error_message: Optional[str] = None
    
class LeadExtracted(SQLModel):
    """
    Response model for /api/extract.
    This is NOT a table (no table=True). It's a validation/response schema.
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    request_summary: Optional[str] = None
    urgency: Optional[str] = None