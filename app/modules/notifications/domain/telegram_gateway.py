# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/domain/telegram_gateway.py
#
# Contrato de las llamadas a la Bot API de Telegram que hace la
# configuración (validar el token, registrar o borrar el webhook y el
# mensaje de prueba). Cada método devuelve None / False si Telegram falló.
# ======================================================================

from __future__ import annotations

from typing import Any, Protocol


class TelegramGateway(Protocol):

    def get_me(self, token: str) -> dict[str, Any] | None:
        """Datos del bot (`username`, …) o None si el token no es válido."""
        ...

    def set_webhook(self, token: str, url: str, secret: str) -> bool:
        ...

    def delete_webhook(self, token: str) -> bool:
        ...

    def send_message(self, token: str, chat_id: str | int, text: str) -> bool:
        ...
