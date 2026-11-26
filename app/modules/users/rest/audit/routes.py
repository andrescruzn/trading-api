# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/audit/routes.py
#
# ENDPOINTS:
# - GET /audit-logs → auditoría HTTP paginada en el servidor (super admin y socio)
#
# NOTAS:
# - Lee las tablas `http_audit_<año>` que escribe AuditMiddleware.
# - No devuelve payloads: solo método, ruta, status, duración, IP, user
#   agent, el `msg` de la respuesta y, en los eventos de login, el correo
#   con el que se intentó entrar. Fechas en UTC con offset (+00:00).
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.contracts.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.common.http import build_error_response, build_paginated_response
from app.common.security.jwt.role_guard import staff_required
from app.common.utils import to_iso_utc
from app.extensions.db import get_db
from app.modules.users.domain import AuditEvent
from app.modules.users.providers.audit_provider import AuditServiceFactory

from .error_messages import AUDIT_ERROR_MESSAGES

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


def get_factory(db: Session = Depends(get_db)) -> AuditServiceFactory:
    return AuditServiceFactory(session=db)


def _event_to_dict(event: AuditEvent) -> dict[str, Any]:
    return {
        # Las tablas son por año: el ID solo es único dentro de su año.
        "key":          f"{event.year}-{event.id}",
        "id":           event.id,
        "year":         event.year,
        "ts":           to_iso_utc(event.ts),
        "user_id":      event.user_id,
        "event_type":   event.event_type,
        "method":       event.method,
        "path":         event.path,
        "status_code":  event.status_code,
        "duration_ms":  event.duration_ms,
        "ip":           event.ip,
        "user_agent":   event.user_agent,
        "response_msg": event.response_msg,
        "login_email":  event.login_email,
    }


# ======================================================================
# GET /audit-logs
# ======================================================================

@router.get("", status_code=200)
def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    user_id: int | None = Query(default=None, gt=0, description="Persona que hizo la petición."),
    event_type: str | None = Query(default=None, max_length=64),
    date_from: datetime | None = Query(default=None, description="Desde (incluida). Sin zona = UTC."),
    date_to: datetime | None = Query(default=None, description="Hasta (excluida). Sin zona = UTC."),
    path: str | None = Query(default=None, max_length=200, description="Texto dentro de la ruta."),
    kind: str | None = Query(default=None, description="read (consultas) | write (cambios)"),
    only_errors: bool = Query(default=False, description="Solo respuestas con status ≥ 400."),
    _identity: dict = Depends(staff_required),
    factory: AuditServiceFactory = Depends(get_factory),
):
    """Eventos de auditoría, del más reciente al más antiguo (super admin y socio)."""
    result = factory.list_audit_events().list(
        page=page,
        page_size=page_size,
        user_id=user_id,
        event_type=event_type,
        date_from=date_from,
        date_to=date_to,
        path=path,
        kind=kind,
        only_errors=only_errors,
    )
    if not result.success:
        return build_error_response(result, AUDIT_ERROR_MESSAGES)

    data = result.data
    return build_paginated_response(
        items=[_event_to_dict(e) for e in data.items],
        total=data.total,
        page=data.page,
        page_size=data.page_size,
    )
