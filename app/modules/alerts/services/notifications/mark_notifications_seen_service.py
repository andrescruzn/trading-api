# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/notifications/mark_notifications_seen_service.py
#
# PROPÓSITO:
# - Marca como vistas las notificaciones del usuario: guarda "ahora" en
#   `users.notifications_seen_at`. Al estar en la cuenta (no en el
#   navegador) el estado se comparte entre dispositivos.
# ======================================================================

from __future__ import annotations

from datetime import datetime

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.users.domain.user_repository import UserRepository


class MarkNotificationsSeenService:
    """Pone `notifications_seen_at = utc_now()` y confirma la transacción."""

    def __init__(self, *, user_repo: UserRepository):
        self._user_repo = user_repo

    def mark_seen(self, user_id: int) -> ServiceResult[datetime]:
        seen_at = utc_now()

        if not self._user_repo.set_notifications_seen_at(user_id, seen_at):
            self._user_repo.rollback()
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        self._user_repo.commit()
        return ServiceResult.ok(data=seen_at)
