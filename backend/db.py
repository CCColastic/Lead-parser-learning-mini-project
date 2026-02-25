from sqlmodel import SQLModel, Session, create_engine
import models
# SQLite file will be created in the backend folder as app.db
sqlite_file_name = "./data/app.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(
    sqlite_url,
    echo=False,
)


def create_db_and_tables() -> None:
    print("Creating database and tables...")
    SQLModel.metadata.create_all(engine)
    print("Database and tables created successfully!")


def get_session():
    """
    FastAPI dependency that provides a DB session per request.
    It will automatically close after the request is done.
    """
    with Session(engine) as session:
        yield session