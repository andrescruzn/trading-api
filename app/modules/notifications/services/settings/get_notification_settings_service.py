# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/services/settings/get_notification_settings_service.py
#
# CASO DE USO:
# - get() → configuración de los canales + si el servidor tiene SMTP
#   (staff: el socio la ve en solo lectura). La ruta nunca devuelve el
#   token ni el secreto del webhook.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from app.common.contracts import ServiceResult
from app.modules.notifications.domain import NotificationSettings, NotificationSettingsReader


@dataclass(frozen=True)
class NotificationSettingsView:
    settings: NotificationSettings
    smtp_configured: bool


class GetNotificationSettingsService:

    def __init__(self, *, reader: NotificationSettingsReader, smtp_configured: bool):
        self._reader = reader
        self._smtp_configured = smtp_configured

    def get(self) -> ServiceResult[NotificationSettingsView]:
        return ServiceResult.ok(
            NotificationSettingsView(settings=self._reader.get(), smtp_configured=self._smtp_configured)
        )
