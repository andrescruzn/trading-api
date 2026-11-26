# app/extensions/db/session.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.extensions.db.config import get_database_url


engine = create_engine(
    get_database_url(),
    future=True,
    pool_pre_ping=True,
)

# ======================================================================
# FIX: Forzar timezone UTC por conexión
# ----------------------------------------------------------------------
# Por qué:
# - Evita que MySQL te guarde/retorne horas en zona local del servidor.
# - Hace consistente que nuestro dominio asuma UTC siempre.
# ======================================================================

@event.listens_for(engine, "connect")
def _set_mysql_session_timezone(dbapi_connection, connection_record) -> None:
    """
    Hook de SQLAlchemy que corre al abrir una conexión nueva.

    Regla:
    - Aseguramos que la sesión MySQL trabaje en UTC.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("SET time_zone = '+00:00';")
    cursor.close()


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
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()