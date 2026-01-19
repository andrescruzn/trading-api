from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.config import get_database_url

# Engine SYNC (no async)
engine = create_engine(
    get_database_url(),
    future=True,
    pool_pre_ping=True,   # evita conexiones muertas
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)

def get_db() -> Session:
    """
    Dependency para FastAPI.
    Abre una sesión por request y la cierra al final.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()