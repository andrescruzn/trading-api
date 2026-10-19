# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/rest/telegram_webhook/routes.py
#
# ENDPOINT:
# - POST /telegram/webhook → updates del bot de Telegram (producción,
#   TELEGRAM_UPDATES_MODE=webhook)
#
# SEGURIDAD:
# - Telegram envía la cabecera X-Telegram-Bot-Api-Secret-Token con el
#   secret_token registrado en setWebhook; se compara en tiempo constante
#   con TELEGRAM_WEBHOOK_SECRET. Sin secreto configurado → 404 siempre.
# - Sin sesión de usuario: la identidad sale del chat vinculado
#   (TelegramUpdateService).
# - Siempre 200 cuando el secreto es correcto: con otro código Telegram
#   reintenta el mismo update.
# - Fuera de la auditoría HTTP (audit_middleware): el cuerpo de /start
#   lleva el código de vinculación.
#
# REGISTRO DEL WEBHOOK (una vez, lo hace el administrador):
#   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
#     -d "url=https://<api>/api/telegram/webhook" \
#     -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>" \
#     -d 'allowed_updates=["message","callback_query"]'
# ======================================================================

from __future__ import annotations

import hmac
import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, Header
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import send
from app.extensions.db import get_db
from app.modules.alerts.providers.telegram_provider import build_telegram_update_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["Telegram"])


def _valid_secret(received: str | None) -> bool:
    expected = settings.TELEGRAM_WEBHOOK_SECRET
    return bool(expected) and hmac.compare_digest((received or "").encode(), expected.encode())


@router.post("/webhook", status_code=200, include_in_schema=False)
def telegram_webhook(
    update: dict[str, Any] = Body(default_factory=dict),
    secret_token: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
    db: Session = Depends(get_db),
):
    if settings.TELEGRAM_UPDATES_MODE != "webhook" or not _valid_secret(secret_token):
        return send(msg="No encontrado.", status_code=404)

    service = build_telegram_update_service(db)
    if service is not None:
        try:
            service.handle(update)
        except Exception:
            logger.exception("Telegram webhook: error procesando el update")

    return send(msg="OK", status_code=200)
