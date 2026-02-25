from fastapi import Depends, FastAPI
from sqlmodel import Session, select, col
from contextlib import asynccontextmanager

from db import create_db_and_tables, get_session, engine
from models import Interaction
from sqlalchemy import desc

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the SQLite DB file and tables if they don't exist
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/history")
def history(limit: int = 50, session: Session = Depends(get_session)):
    """
    Return the most recent interactions (newest first).
    For now it will be empty until we start inserting rows.
    """
    limit = max(1, min(limit, 200))

    statement = select(Interaction).order_by(desc(col(Interaction.id))).limit(limit)
    rows = session.exec(statement).all()

    return rows