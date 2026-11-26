# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/services/settings/update_telegram_settings_service.py
#
# CASO DE USO (super admin):
# - update(...) → guarda la configuración de Telegram.
#
# REGLAS:
# - Token vacío = conservar el guardado (la API nunca lo devuelve).
# - Token nuevo (o sin @usuario guardado): se valida con getMe y el
#   @usuario del bot se toma de la respuesta (TELEGRAM_TOKEN_INVALID).
# - Encender exige token (TELEGRAM_TOKEN_REQUIRED).
# - Chat por defecto opcional: ID numérico (grupos con signo -) o @canal.
# - Modo webhook: URL https pública (misma guarda SSRF que los webhooks de
#   alertas). El secreto lo genera el servidor una vez y se registra con
#   setWebhook; si Telegram falla no se guarda nada (TELEGRAM_WEBHOOK_FAILED).
# - Al salir de webhook o pasar a polling se borra el webhook (best
#   effort): getUpdates no funciona con un webhook registrado.
# ======================================================================

from __future__ import annotations

import re
import secrets

from app.common.contracts import ServiceResult
from app.common.security.url_guard import is_allowed_webhook_url
from app.modules.notifications.domain import (
    UPDATES_MODES,
    NotificationSettings,
    NotificationSettingsRepository,
    TelegramGateway,
)

_CHAT_ID_RE = re.compile(r"^(-?\d{1,20}|@[A-Za-z0-9_]{5,32})$")
_TOKEN_RE = re.compile(r"^\d{5,20}:[A-Za-z0-9_-]{30,64}$")


class UpdateTelegramSettingsService:

    def __init__(self, *, repo: NotificationSettingsRepository, gateway: TelegramGateway):
        self._repo = repo
        self._gateway = gateway

    def update(
        self,
        *,
        enabled: bool,
        bot_token: str | None,
        default_chat_id: str | None,
        updates_mode: str,
        webhook_url: str | None,
        requester_user_id: int,
    ) -> ServiceResult[NotificationSettings]:
        mode = (updates_mode or "").strip().lower()
        if mode not in UPDATES_MODES:
            return ServiceResult.fail(code="TELEGRAM_INVALID_UPDATES_MODE", http_status=422)

        chat_id = (default_chat_id or "").strip() or None
        if chat_id is not None and not _CHAT_ID_RE.match(chat_id):
            return ServiceResult.fail(code="TELEGRAM_INVALID_CHAT_ID", http_status=422)

        current = self._repo.get()
        new_token = (bot_token or "").strip() or None
        if new_token is not None and not _TOKEN_RE.match(new_token):
            return ServiceResult.fail(code="TELEGRAM_TOKEN_INVALID", http_status=422)
        token = new_token or current.telegram_bot_token
        if enabled and not token:
            return ServiceResult.fail(code="TELEGRAM_TOKEN_REQUIRED", http_status=422)

        username = current.telegram_bot_username
        if token and (new_token is not None or not username):
            me = self._gateway.get_me(token)
            if me is None:
                return ServiceResult.fail(code="TELEGRAM_TOKEN_INVALID", http_status=422)
            username = str(me["username"]).lstrip("@")

        url = (webhook_url or "").strip() or None
        secret = current.telegram_webhook_secret
        if mode == "webhook":
            if url is None or not is_allowed_webhook_url(url):
                return ServiceResult.fail(code="TELEGRAM_INVALID_WEBHOOK_URL", http_status=422)
            # Un token nuevo es otro bot: secreto nuevo también
            if not secret or new_token is not None:
                secret = secrets.token_urlsafe(32)
            if enabled and not self._gateway.set_webhook(token, url, secret):
                return ServiceResult.fail(code="TELEGRAM_WEBHOOK_FAILED", http_status=502)
        elif token and (mode == "polling" or current.telegram_updates_mode == "webhook"):
            self._gateway.delete_webhook(token)

        current.telegram_enabled = bool(enabled)
        current.telegram_bot_token = token
        current.telegram_bot_username = username
        current.telegram_default_chat_id = chat_id
        current.telegram_updates_mode = mode
        current.telegram_webhook_url = url
        current.telegram_webhook_secret = secret
        current.updated_by_user_id = int(requester_user_id)
        try:
            saved = self._repo.save(current)
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        return ServiceResult.ok(saved)
