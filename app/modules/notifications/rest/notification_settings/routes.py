# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/rest/notification_settings/routes.py
#
# ENDPOINTS (Administración → Notificaciones):
# - GET  /notification-settings                → configuración (staff; sin secretos)
# - PUT  /notification-settings/telegram       → bot, chat por defecto y modo (super admin)
# - PUT  /notification-settings/email          → enciende / apaga el correo (super admin)
# - POST /notification-settings/telegram/test  → mensaje de prueba (super admin)
# - POST /notification-settings/email/test     → correo de prueba (super admin)
#
# SEGURIDAD:
# - El token del bot y el secreto del webhook nunca salen en la respuesta:
#   solo `token_set`, `token_hint` (últimos 4) y `webhook_secret_set`.
# - `bot_token` está en los campos redactados de la auditoría.
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_success_response
from app.common.security.jwt import staff_required, super_admin_required
from app.common.utils import to_iso_utc
from app.extensions.db import get_db
from app.modules.notifications.domain import NotificationSettings
from app.modules.notifications.providers import NotificationServiceFactory

from .error_messages import (
    EMAIL_TEST_MESSAGE,
    EMAIL_TEST_SUBJECT,
    EMAIL_TEST_TITLE,
    NOTIFICATION_SETTINGS_ERROR_MESSAGES,
    TELEGRAM_TEST_TEXT,
)
from .schemas import UpdateEmailSettingsRequest, UpdateTelegramSettingsRequest

router = APIRouter(prefix="/notification-settings", tags=["Notifications — Settings"])


def get_factory(db: Session = Depends(get_db)) -> NotificationServiceFactory:
    return NotificationServiceFactory(session=db)


def _settings_to_dict(settings: NotificationSettings, smtp_configured: bool) -> dict[str, Any]:
    return {
        "telegram": {
            "enabled":            settings.telegram_enabled,
            "active":             settings.telegram_active,
            "token_set":          bool(settings.telegram_bot_token),
            "token_hint":         settings.token_hint(),
            "bot_username":       settings.telegram_bot_username,
            "default_chat_id":    settings.telegram_default_chat_id,
            "updates_mode":       settings.telegram_updates_mode,
            "webhook_url":        settings.telegram_webhook_url,
            "webhook_secret_set": bool(settings.telegram_webhook_secret),
        },
        "email": {
            "enabled":         settings.email_enabled,
            "smtp_configured": smtp_configured,
        },
        "updated_at": to_iso_utc(settings.updated_at) if settings.updated_at else None,
    }


def _current(factory: NotificationServiceFactory) -> dict[str, Any]:
    view = factory.get_settings().get().data
    return _settings_to_dict(view.settings, view.smtp_configured)


# ======================================================================
# GET /api/notification-settings
# ======================================================================

@router.get("", status_code=200)
def get_notification_settings(
    _identity: dict = Depends(staff_required),
    factory: NotificationServiceFactory = Depends(get_factory),
):
    """Configuración de Telegram y correo (super admin y socio)."""
    return build_success_response(data=_current(factory))


# ======================================================================
# PUT /api/notification-settings/telegram
# ======================================================================

@router.put("/telegram", status_code=200)
def update_telegram_settings(
    payload: UpdateTelegramSettingsRequest,
    identity: dict = Depends(super_admin_required),
    factory: NotificationServiceFactory = Depends(get_factory),
):
    """Guarda el bot, el chat por defecto y el modo de respuestas (super admin)."""
    result = factory.update_telegram().update(
        enabled=payload.enabled,
        bot_token=payload.bot_token,
        default_chat_id=payload.default_chat_id,
        updates_mode=payload.updates_mode,
        webhook_url=payload.webhook_url,
        requester_user_id=int(identity["user_id"]),
    )
    if not result.success:
        return build_error_response(result, NOTIFICATION_SETTINGS_ERROR_MESSAGES)
    return build_success_response(data=_current(factory), msg="Configuración de Telegram guardada.")


# ======================================================================
# PUT /api/notification-settings/email
# ======================================================================

@router.put("/email", status_code=200)
def update_email_settings(
    payload: UpdateEmailSettingsRequest,
    identity: dict = Depends(super_admin_required),
    factory: NotificationServiceFactory = Depends(get_factory),
):
    """Enciende o apaga los avisos por correo (super admin)."""
    result = factory.update_email().update(
        enabled=payload.enabled, requester_user_id=int(identity["user_id"])
    )
    if not result.success:
        return build_error_response(result, NOTIFICATION_SETTINGS_ERROR_MESSAGES)
    msg = "Avisos por correo activados." if payload.enabled else "Avisos por correo desactivados."
    return build_success_response(data=_current(factory), msg=msg)


# ======================================================================
# POST /api/notification-settings/telegram/test
# ======================================================================

@router.post("/telegram/test", status_code=200)
def send_telegram_test(
    identity: dict = Depends(super_admin_required),
    factory: NotificationServiceFactory = Depends(get_factory),
):
    """Mensaje de prueba a tu chat vinculado o, si no tienes, al chat por defecto."""
    result = factory.send_telegram_test().send(
        requester_user_id=int(identity["user_id"]), text=TELEGRAM_TEST_TEXT
    )
    if not result.success:
        return build_error_response(result, NOTIFICATION_SETTINGS_ERROR_MESSAGES)
    msg = (
        "Mensaje de prueba enviado a tu chat de Telegram."
        if result.data["target"] == "own_chat"
        else "Mensaje de prueba enviado al chat por defecto."
    )
    return build_success_response(data=result.data, msg=msg)


# ======================================================================
# POST /api/notification-settings/email/test
# ======================================================================

@router.post("/email/test", status_code=200)
def send_email_test(
    identity: dict = Depends(super_admin_required),
    factory: NotificationServiceFactory = Depends(get_factory),
):
    """Correo de prueba a tu propio correo (super admin)."""
    result = factory.send_email_test().send(
        requester_user_id=int(identity["user_id"]),
        subject=EMAIL_TEST_SUBJECT,
        title=EMAIL_TEST_TITLE,
        message=EMAIL_TEST_MESSAGE,
    )
    if not result.success:
        return build_error_response(result, NOTIFICATION_SETTINGS_ERROR_MESSAGES)
    return build_success_response(
        data=result.data, msg=f"Correo de prueba enviado a {result.data['to_email']}."
    )
