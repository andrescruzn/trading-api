# app/extensions/db/session.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.extensions.db.config import get_database_url


# ----------------------------------------------------------------------
# Engine SYNC (no async)
# ----------------------------------------------------------------------
engine = create_engine(
    get_database_url(),
    future=True,
    pool_pre_ping=True,  # evita conexiones muertas
)

# ----------------------------------------------------------------------
# Session factory
# ----------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para FastAPI.
    Abre una sesión por request y la cierra al final.

    Tipado:
    - Es un generator porque usa `yield`.
    - Por eso retorna Generator[Session, None, None].
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()