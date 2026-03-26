# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/rest/alert_events/routes.py
#
# ENDPOINTS:
# - GET /api/alert-events   → historial de eventos disparados
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import build_list_response
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.providers import AlertServiceFactory, get_alert_factory

router = APIRouter(prefix="/api/alert-events", tags=["Alert Events"])


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
    identity: dict = Depends(token_required_actual),
    factory: AlertServiceFactory = Depends(get_factory),
):
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)
    user_id = identity.get("user_id")

    result = factory.list_alert_events().list(
        user_id=user_id,
        is_admin=is_admin,
        limit=limit,
        from_ts=from_ts,
    )
    return build_list_response(
        items=[_event_to_dict(e) for e in (result.data or [])],
        msg="OK",
    )
