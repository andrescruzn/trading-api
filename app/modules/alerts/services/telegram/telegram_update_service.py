# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/telegram/telegram_update_service.py
#
# PROPÓSITO:
# - Procesar un "update" de Telegram (webhook o polling):
#   - "/start <código>"  → vincular el chat a la cuenta (TelegramLinkService)
#   - botón sig:a:<id>   → aprobar la señal (ExecuteSignalService.execute)
#   - botón sig:r:<id>   → rechazar la señal (ExecuteSignalService.reject)
#
# SEGURIDAD:
# - Solo chats privados. El usuario se identifica por el chat vinculado;
#   la señal debe ser de un agente de ese usuario (owner_id = user.id,
#   también si es admin: desde Telegram cada quien decide lo suyo).
# - El texto de la persona nunca se ejecuta ni se interpreta: solo se
#   reconocen "/start <código>" y los callback_data con formato fijo.
# ======================================================================

from __future__ import annotations

import html
import logging
import re
from typing import TYPE_CHECKING, Any, Callable

from app.common.contracts import ServiceResult
from app.modules.alerts.channels.telegram_replier import TelegramReplier
from app.modules.users.domain import UserRepository

if TYPE_CHECKING:
    from app.modules.users.services.telegram import TelegramLinkService

logger = logging.getLogger(__name__)

_CALLBACK_RE = re.compile(r"^sig:(a|r):(\d{1,18})$")
_START_RE = re.compile(r"^/start(?:@\w+)?(?:\s+([A-Za-z0-9_-]{1,64}))?\s*$")

# (acción "approve" | "reject", signal_id, user_id) → ServiceResult
SignalDecider = Callable[[str, int, int], ServiceResult[Any]]


class TelegramUpdateService:
    """Atiende los mensajes y botones que llegan al bot de Telegram."""

    def __init__(
        self,
        *,
        user_repo: UserRepository,
        link_service: "TelegramLinkService",
        decide: SignalDecider,
        replier: TelegramReplier,
    ):
        self._user_repo = user_repo
        self._link_service = link_service
        self._decide = decide
        self._replier = replier

    def handle(self, update: dict[str, Any]) -> None:
        if not isinstance(update, dict):
            return
        if isinstance(update.get("callback_query"), dict):
            self._on_callback(update["callback_query"])
        elif isinstance(update.get("message"), dict):
            self._on_message(update["message"])

    # ------------------------------------------------------------------
    # Mensajes: solo "/start [código]" en chats privados
    # ------------------------------------------------------------------

    def _on_message(self, message: dict[str, Any]) -> None:
        chat = message.get("chat") or {}
        if chat.get("type") != "private" or not isinstance(chat.get("id"), int):
            return

        match = _START_RE.match(str(message.get("text") or ""))
        if match is None:
            return

        code = match.group(1)
        if not code:
            self._replier.link_result(chat["id"], "TELEGRAM_START_WITHOUT_CODE")
            return

        result = self._link_service.confirm(code=code, chat_id=chat["id"])
        self._replier.link_result(
            chat["id"], "TELEGRAM_LINKED" if result.success else "TELEGRAM_LINK_INVALID"
        )

    # ------------------------------------------------------------------
    # Botones Aprobar / Rechazar
    # ------------------------------------------------------------------

    def _on_callback(self, callback: dict[str, Any]) -> None:
        callback_id = str(callback.get("id") or "")
        message = callback.get("message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id") if isinstance(chat.get("id"), int) else None
        message_id = message.get("message_id") if isinstance(message.get("message_id"), int) else None

        def reply(code: str) -> None:
            self._replier.decision_result(
                callback_query_id=callback_id,
                chat_id=chat_id,
                message_id=message_id,
                original_html=_original_html(message),
                code=code,
            )

        match = _CALLBACK_RE.match(str(callback.get("data") or ""))
        if not callback_id or match is None or chat_id is None or chat.get("type") != "private":
            return

        user = self._user_repo.get_by_telegram_chat_id(chat_id)
        if user is None or not user.is_active():
            reply("CHAT_NOT_LINKED")
            return

        action = "approve" if match.group(1) == "a" else "reject"
        signal_id = int(match.group(2))
        try:
            result = self._decide(action, signal_id, user.id)
        except Exception:
            logger.exception("Telegram: error al decidir la señal %s", signal_id)
            reply("UNEXPECTED")
            return

        if result.success:
            reply("SIGNAL_EXECUTED" if action == "approve" else "SIGNAL_REJECTED")
        else:
            reply(result.error.code)


def _original_html(message: dict[str, Any]) -> str | None:
    """
    Texto original del aviso para reescribirlo con el resultado.

    Telegram devuelve el texto plano (sin HTML); se escapa para volver a
    enviarlo con parse_mode HTML sin que un `<` lo rompa.
    """
    text = message.get("text")
    return html.escape(text) if isinstance(text, str) else None
