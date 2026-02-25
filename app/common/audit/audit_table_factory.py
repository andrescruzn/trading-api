# -*- coding: utf-8 -*-

# ======================================================================
# app/common/audit/audit_table_factory.py
#
# PROPÓSITO:
# - Crear y cachear tablas SQLAlchemy Core por año (http_audit_YYYY).
# - Usa double-check locking para thread safety sin bloquear en cada request.
#
# DECISIÓN:
# - SQLAlchemy Core Table() — NO DeclarativeBase — porque el nombre
#   de tabla es dinámico y no podemos definirlo en tiempo de clase.
# - MetaData propio para no contaminar models_registry.
# - checkfirst=True en create → idempotente aunque la tabla ya exista.
# ======================================================================

from __future__ import annotations

import threading
from typing import Any

from sqlalchemy import (
    BigInteger,
    Column,
    Index,
    Integer,
    JSON,
    MetaData,
    SmallInteger,
    String,
    Table,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP as MySQLTIMESTAMP
from sqlalchemy.engine import Engine

# ======================================================================
# Metadata y caché aislados del ORM principal
# ======================================================================

_metadata = MetaData()
_table_cache: dict[int, Table] = {}
_lock = threading.Lock()


def _build_table_definition(year: int) -> Table:
    """
    Define la estructura de la tabla http_audit_{year}.

    Se usa extend_existing=True para evitar error si MetaData
    ya registró la tabla en una llamada anterior.
    """
    table_name = f"http_audit_{year}"
    return Table(
        table_name,
        _metadata,
        Column("id", BigInteger, primary_key=True, autoincrement=True),
        Column("user_id", BigInteger, nullable=True),
        Column("event_type", String(64), nullable=False),
        Column("method", String(10), nullable=False),
        Column("path", String(512), nullable=False),
        Column("status_code", SmallInteger, nullable=False),
        Column("ip", String(64), nullable=True),
        Column("user_agent", String(512), nullable=True),
        Column("referer", String(512), nullable=True),
        Column("request_payload", JSON, nullable=True),
        Column("response_payload", JSON, nullable=True),
        Column("duration_ms", Integer, nullable=True),
        Column(
            "ts",
            MySQLTIMESTAMP(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
        Index(f"idx_{table_name}_ts", "ts"),
        Index(f"idx_{table_name}_user_ts", "user_id", "ts"),
        Index(f"idx_{table_name}_event_type_ts", "event_type", "ts"),
        extend_existing=True,
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )


def get_or_create_table(year: int, engine: Engine) -> Table:
    """
    Retorna la Table para el año dado, creándola en BD si no existe.

    Patrón double-check locking:
    1. Check sin lock → retorno rápido para el 99% de requests.
    2. Adquiere lock → re-verifica → crea si sigue ausente.

    Esto garantiza thread safety sin bloquear en cada request.
    """
    # ------------------------------------------------------------------
    # Fast path: ya está en caché
    # ------------------------------------------------------------------
    if year in _table_cache:
        return _table_cache[year]

    # ------------------------------------------------------------------
    # Slow path: adquirir lock y re-verificar
    # ------------------------------------------------------------------
    with _lock:
        if year in _table_cache:
            return _table_cache[year]

        table = _build_table_definition(year)

        with engine.begin() as conn:
            table.create(bind=conn, checkfirst=True)

        _table_cache[year] = table
        return table
