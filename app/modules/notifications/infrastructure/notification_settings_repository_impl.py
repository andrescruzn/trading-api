# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/infrastructure/notification_settings_repository_impl.py
#
# NOTAS:
# - Token y secreto del webhook se cifran con CredentialsCipher (Fernet,
#   misma clave que las credenciales de exchange). Un valor que no se
#   puede descifrar (clave rotada sin CREDENTIALS_PREVIOUS_KEYS) se trata
#   como "sin valor": Telegram queda inactivo en vez de romper el flujo.
# - `get()` usa session.get: dentro de un request la fila queda en el
#   identity map, así que leerla desde varios servicios no repite la query.
# ======================================================================

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.common.security.credentials_cipher import CredentialsCipher
from app.common.utils import ensure_aware_utc
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository
from app.modules.notifications.domain.notification_settings_entity import NotificationSettings
from app.modules.notifications.infrastructure.notification_settings_model import (
    NotificationSettingsModel,
)

logger = logging.getLogger(__name__)

_SETTINGS_ROW_ID = 1
_SECRET_KEY = "value"


class SqlAlchemyNotificationSettingsRepository(SqlAlchemyRepository):

    def __init__(self, session: Session, cipher: CredentialsCipher | None = None):
        self._session = session
        self._cipher = cipher

    def _get_cipher(self) -> CredentialsCipher:
        if self._cipher is None:
            self._cipher = CredentialsCipher.from_settings()
        return self._cipher

    def _encrypt(self, value: str | None) -> str | None:
        if not value:
            return None
        return self._get_cipher().encrypt_dict({_SECRET_KEY: value})

    def _decrypt(self, token: str | None, field: str) -> str | None:
        if not token:
            return None
        try:
            return self._get_cipher().decrypt(token).get(_SECRET_KEY) or None
        except Exception:
            logger.error("notification_settings: no se pudo descifrar %s", field)
            return None

    def _to_domain(self, model: NotificationSettingsModel) -> NotificationSettings:
        return NotificationSettings(
            telegram_enabled=bool(model.telegram_enabled),
            telegram_bot_token=self._decrypt(model.telegram_bot_token_enc, "el token"),
            telegram_bot_username=model.telegram_bot_username,
            telegram_default_chat_id=model.telegram_default_chat_id,
            telegram_updates_mode=model.telegram_updates_mode or "off",
            telegram_webhook_url=model.telegram_webhook_url,
            telegram_webhook_secret=self._decrypt(
                model.telegram_webhook_secret_enc, "el secreto del webhook"
            ),
            email_enabled=bool(model.email_enabled),
            updated_by_user_id=model.updated_by_user_id,
            updated_at=ensure_aware_utc(model.updated_at),
        )

    def get(self) -> NotificationSettings:
        model = self._session.get(NotificationSettingsModel, _SETTINGS_ROW_ID)
        return NotificationSettings() if model is None else self._to_domain(model)

    def save(self, settings: NotificationSettings) -> NotificationSettings:
        model = self._session.get(NotificationSettingsModel, _SETTINGS_ROW_ID)
        if model is None:
            model = NotificationSettingsModel(id=_SETTINGS_ROW_ID)
            self._session.add(model)
        model.telegram_enabled = settings.telegram_enabled
        model.telegram_bot_token_enc = self._encrypt(settings.telegram_bot_token)
        model.telegram_bot_username = settings.telegram_bot_username
        model.telegram_default_chat_id = settings.telegram_default_chat_id
        model.telegram_updates_mode = settings.telegram_updates_mode
        model.telegram_webhook_url = settings.telegram_webhook_url
        model.telegram_webhook_secret_enc = self._encrypt(settings.telegram_webhook_secret)
        model.email_enabled = settings.email_enabled
        model.updated_by_user_id = settings.updated_by_user_id
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
