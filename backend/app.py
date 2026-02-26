from contextlib import asynccontextmanager
from datetime import datetime
import json
import os

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import desc
from sqlmodel import Session, col, select, delete

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi import _rate_limit_exceeded_handler

from db import create_db_and_tables, get_session
from llm import call_and_parse_lead
from models import Interaction, InteractionOut, LeadExtracted


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


# 1) Create limiter (key function decides how we identify a client: here by IP)
limiter = Limiter(key_func=get_remote_address)

# 2) Attach limiter to app.state (SlowAPI integration requirement)
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter

# 3) Add middleware that intercepts requests and enforces limits
app.add_middleware(SlowAPIMiddleware)

# 4) Register exception handler so RateLimitExceeded becomes a proper 429 response
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class ExtractRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/history", response_model=list[InteractionOut])
def history(limit: int = 50, session: Session = Depends(get_session)):
    limit = max(1, min(limit, 200))
    statement = select(Interaction).order_by(desc(col(Interaction.id))).limit(limit)
    rows = session.exec(statement).all()

    out: list[InteractionOut] = []

    for r in rows:
        parsed_obj = None
        if r.parsed_json:
            try:
                parsed_obj = LeadExtracted.model_validate(json.loads(r.parsed_json))
            except Exception:
                # If parsing fails, we still return the raw parsed_json string.
                parsed_obj = None

        out.append(
            InteractionOut(
                id=r.id or 0,
                created_at=r.created_at,
                input_text=r.input_text,
                status=r.status,
                error_message=r.error_message,
                parsed_json=r.parsed_json,
                parsed=parsed_obj,
            )
        )

    return out


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


# Rate limit: 5 requests per minute per IP (tune later)
@app.post("/api/extract", response_model=LeadExtracted)
@limiter.limit("5/minute")
def extract(request: Request, req: ExtractRequest, session: Session = Depends(get_session)):
    """
    Main endpoint: calls DeepSeek and returns structured JSON.
    Rate limited to protect cost & stability.
    """
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    try:
        raw, parsed = call_and_parse_lead(text, model=model, max_retries=2)
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