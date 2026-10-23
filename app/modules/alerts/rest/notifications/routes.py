# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/rest/notifications/routes.py
#
# Campana de notificaciones del header (feed de alert_events del usuario).
#
# ENDPOINTS:
# - GET  /api/notifications?limit=20 → últimos eventos + unread_count
# - POST /api/notifications/seen     → marca todo como visto (en la cuenta)
#
# NOTAS:
# - Solo eventos del usuario autenticado, también para un admin.
# - `ts` sale en UTC con offset (`+00:00`) para que el navegador lo
#   convierta a la hora de Colombia.
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_success_response
from app.common.security.jwt import token_required_actual
from app.common.utils import to_iso_utc
from app.extensions.db import get_db
from app.modules.alerts.providers import AlertServiceFactory, get_alert_factory
from app.modules.alerts.services.notifications import Notification

from .error_messages import NOTIFICATION_ERROR_MESSAGES

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_factory(db: Session = Depends(get_db)) -> AlertServiceFactory:
    return get_alert_factory(db)


def _notification_to_dict(n: Notification) -> dict[str, Any]:
    e = n.event
    return {
        "id":       e.id,
        "ts":       to_iso_utc(e.ts),
        "title":    e.title,
        "message":  e.message,
        "severity": e.severity,
        "bot_id":   e.bot_id,
        "is_new":   n.is_new,
    }


# ======================================================================
# GET /api/notifications
# ======================================================================

@router.get("", status_code=200)
def list_notifications(
    limit: int = Query(default=20, ge=1, le=50),
    identity: dict = Depends(token_required_actual),
    factory: AlertServiceFactory = Depends(get_factory),
):
    result = factory.list_notifications().list(user_id=int(identity["user_id"]), limit=limit)
    if not result.success:
        return build_error_response(result, NOTIFICATION_ERROR_MESSAGES)

    feed = result.data
    return build_success_response(
        data={
            "items":        [_notification_to_dict(n) for n in feed.items],
            "unread_count": feed.unread_count,
            "seen_at":      to_iso_utc(feed.seen_at),
        },
    )


# ======================================================================
# POST /api/notifications/seen
# ======================================================================

@router.post("/seen", status_code=200)
def mark_notifications_seen(
    identity: dict = Depends(token_required_actual),
    factory: AlertServiceFactory = Depends(get_factory),
):
    result = factory.mark_notifications_seen().mark_seen(user_id=int(identity["user_id"]))
    if not result.success:
        return build_error_response(result, NOTIFICATION_ERROR_MESSAGES)

    return build_success_response(
        data={"seen_at": to_iso_utc(result.data)},
        msg="Notificaciones marcadas como vistas.",
    )
