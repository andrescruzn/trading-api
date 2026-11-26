# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/domain/notification_settings_repository.py
#
# Contratos:
# - NotificationSettingsReader: lo único que necesitan los demás módulos
#   (alerts, users, bots) para saber si Telegram y el correo están activos.
# - NotificationSettingsRepository: lectura + escritura (solo este módulo).
# ======================================================================

from __future__ import annotations

from typing import Protocol

from app.common.contracts import TransactionalRepository
from app.modules.notifications.domain.notification_settings_entity import NotificationSettings


class NotificationSettingsReader(Protocol):

    def get(self) -> NotificationSettings:
        """Los ajustes guardados, o los valores por defecto si aún no hay fila."""
        ...


class NotificationSettingsRepository(NotificationSettingsReader, TransactionalRepository, Protocol):

    def save(self, settings: NotificationSettings) -> NotificationSettings:
        """Crea o reemplaza la única fila (sin commit)."""
        ...
