"""SQLite-backed engine for the model registry.

Deliberately a single SQLite file, not a database server: this registry is
scoped as a single-writer demo/reference implementation (see README). Swap
`DATABASE_URL` for a Postgres URL if concurrent writers become a real
requirement -- SQLModel/SQLAlchemy make that a config change, not a rewrite.
"""
import os
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

DB_PATH = Path(os.environ.get("REGISTRY_DB_PATH", Path(__file__).resolve().parents[2] / "registry.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
