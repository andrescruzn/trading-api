# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/infrastructure/telegram_api.py
#
# - telegram_api(token, method, payload): única puerta a la Bot API de
#   Telegram (la usan este módulo y alerts). Vive aquí porque
#   notifications no depende de ningún otro módulo.
# - HttpTelegramGateway: TelegramGateway para la configuración.
#
# SEGURIDAD:
# - El token va en la URL de la Bot API: nunca se loguea la URL ni el
#   texto de la excepción de httpx (que la incluye), solo su tipo.
# ======================================================================

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10


def telegram_api(token: str, method: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """
    POST a https://api.telegram.org/bot<token>/<method>.

    Returns:
        El campo `result` si Telegram respondió ok, o None.
    """
    try:
        import httpx

        resp = httpx.post(
            f"https://api.telegram.org/bot{token}/{method}",
            json=payload,
            timeout=_TIMEOUT_SECONDS,
        )
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.status_code != 200 or not body.get("ok"):
            logger.warning(
                "Telegram %s HTTP %s: %s",
                method,
                resp.status_code,
                str(body.get("description", ""))[:200],
            )
            return None
        result = body.get("result")
        return result if isinstance(result, dict) else {"value": result}
    except Exception as exc:
        logger.error("Telegram %s %s", method, type(exc).__name__)
        return None


class HttpTelegramGateway:
    """TelegramGateway sobre telegram_api."""

    def get_me(self, token: str) -> dict[str, Any] | None:
        result = telegram_api(token, "getMe", {})
        return result if result and result.get("username") else None

    def set_webhook(self, token: str, url: str, secret: str) -> bool:
        return telegram_api(
            token,
            "setWebhook",
            {
                "url": url,
                "secret_token": secret,
                "allowed_updates": ["message", "callback_query"],
            },
        ) is not None

    def delete_webhook(self, token: str) -> bool:
        return telegram_api(token, "deleteWebhook", {}) is not None

    def send_message(self, token: str, chat_id: str | int, text: str) -> bool:
        return telegram_api(token, "sendMessage", {"chat_id": chat_id, "text": text}) is not None
