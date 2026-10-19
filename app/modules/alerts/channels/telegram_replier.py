# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/telegram_replier.py
#
# PROPÓSITO:
# - Responder en Telegram lo que decidió el TelegramUpdateService: el
#   servicio entrega códigos y este canal los convierte en texto
#   (telegram_messages) y llama a la Bot API.
# ======================================================================

from __future__ import annotations

import html

from app.modules.alerts.channels.telegram_channel import telegram_api
from app.modules.alerts.channels.telegram_messages import LINK_MESSAGES, decision_text

# Telegram corta los mensajes en 4096 caracteres
_MAX_MESSAGE = 4000


class TelegramReplier:
    """Respuestas del bot de Telegram a mensajes y botones."""

    def __init__(self, token: str):
        self._token = token

    def link_result(self, chat_id: int, code: str) -> None:
        telegram_api(self._token, "sendMessage", {"chat_id": chat_id, "text": LINK_MESSAGES[code]})

    def decision_result(
        self,
        *,
        callback_query_id: str,
        chat_id: int | None,
        message_id: int | None,
        original_html: str | None,
        code: str,
    ) -> None:
        text = decision_text(code)
        telegram_api(
            self._token,
            "answerCallbackQuery",
            {"callback_query_id": callback_query_id, "text": text[:200]},
        )
        if chat_id is None or message_id is None:
            return
        # Se agrega el resultado al mensaje y se quitan los botones (sin
        # reply_markup, Telegram elimina el teclado)
        body = original_html or ""
        telegram_api(
            self._token,
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"{body}\n\n<b>{html.escape(text)}</b>"[:_MAX_MESSAGE],
                "parse_mode": "HTML",
            },
        )
