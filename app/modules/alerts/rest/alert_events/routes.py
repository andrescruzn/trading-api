# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/rest/alert_events/routes.py
#
# ENDPOINTS:
# - GET /api/alert-events   → historial de eventos disparados (el más reciente primero).
#                             Con `page` responde paginado {items, pagination}
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.contracts import PageRequest
from app.common.contracts.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.common.http import build_list_response, build_paginated_response
from app.common.security.jwt import is_staff, token_required_actual
from app.extensions.db import get_db
from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.providers import AlertServiceFactory, get_alert_factory

router = APIRouter(prefix="/alert-events", tags=["Alert Events"])


def get_factory(db: Session = Depends(get_db)) -> AlertServiceFactory:
    return get_alert_factory(db)


def _event_to_dict(e: AlertEvent) -> dict[str, Any]:
    return {
        "id":              e.id,
        "alert_rule_id":   e.alert_rule_id,
        "user_id":         e.user_id,
        "bot_id":          e.bot_id,
        "ts":              e.ts.isoformat() if e.ts else None,
        "severity":        e.severity,
        "title":           e.title,
        "message":         e.message,
        "payload":         e.payload,
        "delivery_status": e.delivery_status,
    }


# ======================================================================
# GET /api/alert-events
# ======================================================================

@router.get("", status_code=200)
def list_alert_events(
    limit: int = Query(default=50, ge=1, le=500),
    from_ts: datetime | None = Query(default=None),
    user_id: int | None = Query(default=None, gt=0, description="Solo staff: eventos de ese usuario."),
    page: int | None = Query(default=None, ge=1, description="Activa la respuesta paginada."),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    identity: dict = Depends(token_required_actual),
    factory: AlertServiceFactory = Depends(get_factory),
):
    """
    Staff: todos los eventos (o los de `user_id`). El resto: los suyos.
    Sin `page`: `data` es la lista (hasta `limit`). Con `page`: `data` es
    `{items, pagination}` y `limit` se ignora.
    """
    scope = {
        "user_id":      identity.get("user_id"),
        "is_admin":     is_staff(identity),
        "from_ts":      from_ts,
        "owner_filter": user_id,
    }
    service = factory.list_alert_events()

    if page is not None:
        result = service.list_page(page=PageRequest.of(page, page_size), **scope)
        return build_paginated_response(
            items=[_event_to_dict(e) for e in result.data.items],
            total=result.data.total,
            page=result.data.page,
            page_size=result.data.page_size,
        )

    result = service.list(limit=limit, **scope)
    return build_list_response(
        items=[_event_to_dict(e) for e in (result.data or [])],
        msg="OK",
    )
