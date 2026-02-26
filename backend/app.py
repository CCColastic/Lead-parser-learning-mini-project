from contextlib import asynccontextmanager
from datetime import datetime
import json
import os

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc
from sqlmodel import Session, col, select, delete

from db import create_db_and_tables, get_session
from llm import call_and_parse_lead
from models import Interaction, LeadExtracted


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


class ExtractRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/history")
def history(limit: int = 50, session: Session = Depends(get_session)):
    limit = max(1, min(limit, 200))
    statement = select(Interaction).order_by(desc(col(Interaction.id))).limit(limit)
    rows = session.exec(statement).all()
    return rows


@app.delete("/api/history")
def clear_history(session: Session = Depends(get_session)):
    """
    Development helper: delete all Interaction rows.
    We'll likely protect this later (API key) or remove it in production.
    """
    session.exec(delete(Interaction))
    session.commit()
    return {"deleted": True}


@app.post("/api/debug/seed")
def seed(session: Session = Depends(get_session)):
    row = Interaction(
        input_text="Hi, I'm Sam from Acme. Email: sam@acme.com. Need a demo.",
        raw_model_output=None,
        parsed_json=None,
        status="ok",
        error_message=None,
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    return {
        "inserted": True,
        "id": row.id,
        "created_at": row.created_at.isoformat()
        if isinstance(row.created_at, datetime)
        else str(row.created_at),
    }


@app.post("/api/extract", response_model=LeadExtracted)
def extract(req: ExtractRequest, session: Session = Depends(get_session)):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    try:
        raw, parsed = call_and_parse_lead(text, model=model, max_retries=2)

        # Validate that parsed JSON matches our expected schema
        extracted = LeadExtracted.model_validate(parsed)

        interaction = Interaction(
            input_text=text,
            raw_model_output=raw,
            parsed_json=json.dumps(extracted.model_dump(), ensure_ascii=False),
            status="ok",
            error_message=None,
        )
        session.add(interaction)
        session.commit()

        return extracted

    except Exception as e:
        # Store failure for debugging
        interaction = Interaction(
            input_text=text,
            raw_model_output="",
            parsed_json=None,
            status="error",
            error_message=str(e),
        )
        session.add(interaction)
        session.commit()

        raise HTTPException(status_code=500, detail=str(e))