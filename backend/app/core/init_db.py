"""
Standalone database initialization.

Run directly to create all tables without starting the web server:
    python -m app.core.init_db

The FastAPI app also calls this same create_all() automatically on
startup (see app/main.py), so in normal development you don't need to run
this manually — it's here for scripting, CI, and explicit "reset my db"
workflows.
"""
from app.core.database import Base, engine
import app.models  # noqa: F401  ensures every table is registered on Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print(f"Initialized tables: {sorted(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    init_db()
