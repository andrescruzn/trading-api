# -*- coding: utf-8 -*-

# ======================================================================
# app/common/audit/audit_repository.py
#
# PROPÓSITO:
# - Insertar registros en la tabla http_audit_{year} correspondiente.
# - Silencia toda excepción — la auditoría nunca rompe requests.
#
# DISEÑO:
# - Usa engine directamente (no get_db) porque se invoca desde
#   un hilo daemon, fuera del ciclo de vida de un request FastAPI.
# ======================================================================

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.engine import Engine

from app.common.audit.audit_table_factory import get_or_create_table

logger = logging.getLogger(__name__)

# ======================================================================
# Límites de longitud de campos
# ======================================================================
_MAX_PATH = 512
_MAX_IP = 64
_MAX_USER_AGENT = 512
_MAX_REFERER = 512


class AuditRepository:
    """
    Repositorio para registros de auditoría HTTP.

    Usa SQLAlchemy Core (no ORM) con la tabla dinámica del año actual.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def insert(
        self,
        *,
        user_id: int | None,
        event_type: str,
        method: str,
        path: str,
        status_code: int,
        ip: str | None,
        user_agent: str | None,
        referer: str | None,
        request_payload: dict | None,
        response_payload: dict | None,
        duration_ms: int | None,
    ) -> None:
        """
        Inserta un registro de auditoría.

        Silencia toda excepción para no afectar la latencia del usuario.
        """
        try:
            year = datetime.now(timezone.utc).year
            table = get_or_create_table(year=year, engine=self._engine)

            with self._engine.begin() as conn:
                conn.execute(
                    table.insert().values(
                        user_id=user_id,
                        event_type=event_type,
                        method=method,
                        path=(path or "")[:_MAX_PATH],
                        status_code=status_code,
                        ip=(ip or "")[:_MAX_IP] if ip else None,
                        user_agent=(user_agent or "")[:_MAX_USER_AGENT] if user_agent else None,
                        referer=(referer or "")[:_MAX_REFERER] if referer else None,
                        request_payload=request_payload,
                        response_payload=response_payload,
                        duration_ms=duration_ms,
                    )
                )
        except Exception as exc:
            # La auditoría nunca debe bloquear el flujo del request.
            logger.warning("audit insert failed: %s", exc, exc_info=False)
