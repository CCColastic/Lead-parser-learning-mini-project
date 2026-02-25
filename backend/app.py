from contextlib import asynccontextmanager
from datetime import datetime
import json
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import desc
from sqlmodel import Session, col, select, delete
from pydantic import BaseModel
from db import create_db_and_tables, get_session
from models import Interaction, LeadExtracted

class ExtractRequest(BaseModel):
    text: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"ok": True}

@app.get("/api/history")
def history(limit: int = 50, session: Session = Depends(get_session)):
    limit = max(1, min(limit, 200))
    statement = select(Interaction).order_by(desc(col(Interaction.id))).limit(limit)
    rows = session.exec(statement).all()
    return rows


@app.post("/api/debug/seed")
def seed(session: Session = Depends(get_session)):
    """
    Debug endpoint: inserts a sample row so we can confirm DB writes work.
    We'll remove or disable this later.
    """
    row = Interaction(
        input_text="Hi, I'm Sam from Acme. Email: sam@acme.com. Need a demo.",
        raw_model_output=None,
        parsed_json=None,
        status="ok",
        error_message=None,
    )
    session.add(row)
    session.commit()
    session.refresh(row)  # loads generated fields like id from the DB

    return {
        "inserted": True,
        "id": row.id,
        "created_at": row.created_at.isoformat() if isinstance(row.created_at, datetime) else str(row.created_at),
    }

@app.post("/api/extract", response_model=LeadExtracted)
def extract(req: ExtractRequest, session: Session = Depends(get_session)):
    """
    Main endpoint (stubbed for now):
    - Accepts free text
    - Returns structured lead info (fake/stub)
    - Saves interaction to DB so history works
    """
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    
    extracted = LeadExtracted(
        name = None,
        email="sam@acme.com" if "@" in text else None,
        phone = None,
        company = "Acme" if "acme" in text.lower() else None,
        request_summary="User is asking for a demo",
        urgency="medium",
    )
    
    interaction = Interaction(
        input_text=text,
        raw_model_output="(stubbed extractor - no LLM yet)",
        parsed_json=json.dumps(extracted.model_dump(), ensure_ascii=False),
        status="ok",
        error_message=None,
    )
    session.add(interaction)
    session.commit()
    session.refresh(interaction)  # loads generated fields like id from the DB
    return extracted

@app.delete("/api/history")
def clear_history(session: Session = Depends(get_session)):
    """
    Development helper: delete all Interaction rows.
    We'll likely protect this later (API key) or remove it in production.
    """
    session.exec(delete(Interaction))
    session.commit()
    return {"deleted": True}