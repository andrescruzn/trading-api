# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/services/settings/update_email_settings_service.py
#
# CASO DE USO (super admin):
# - update(enabled) → enciende o apaga los avisos por correo (alertas,
#   señales por aprobar, señales compartidas y avisos del fondo). El
#   código de acceso y las invitaciones siempre salen.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.notifications.domain import NotificationSettings, NotificationSettingsRepository


class UpdateEmailSettingsService:

    def __init__(self, *, repo: NotificationSettingsRepository):
        self._repo = repo

    def update(self, *, enabled: bool, requester_user_id: int) -> ServiceResult[NotificationSettings]:
        current = self._repo.get()
        current.email_enabled = bool(enabled)
        current.updated_by_user_id = int(requester_user_id)
        try:
            saved = self._repo.save(current)
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        return ServiceResult.ok(saved)
