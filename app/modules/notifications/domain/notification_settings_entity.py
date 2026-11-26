# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/domain/notification_settings_entity.py
#
# Entidad de dominio: NotificationSettings (canales de notificación del
# sistema). Una sola fila, la edita el super admin desde la app:
# - Telegram: bot (token, @usuario), chat por defecto y cómo llegan las
#   respuestas (off | polling | webhook).
# - Email: interruptor de los avisos por correo (el SMTP vive en .env).
#
# Los valores van en claro: cifrar el token y el secreto del webhook es
# cosa del repositorio.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# off: no se procesan respuestas · polling: el scheduler pide los updates
# (desarrollo) · webhook: Telegram llama POST /api/telegram/webhook (producción)
UPDATES_MODES: tuple[str, ...] = ("off", "polling", "webhook")


@dataclass
class NotificationSettings:
    telegram_enabled: bool = False
    telegram_bot_token: str | None = None
    telegram_bot_username: str | None = None
    telegram_default_chat_id: str | None = None
    telegram_updates_mode: str = "off"
    telegram_webhook_url: str | None = None
    telegram_webhook_secret: str | None = None
    # Por defecto encendido: antes de este ajuste el correo salía siempre que
    # hubiera SMTP configurado.
    email_enabled: bool = True
    updated_by_user_id: int | None = None
    updated_at: datetime | None = None

    @property
    def telegram_active(self) -> bool:
        """Telegram encendido y con token: se puede enviar y recibir."""
        return self.telegram_enabled and bool(self.telegram_bot_token)

    @property
    def telegram_token(self) -> str:
        """El token si Telegram está activo; "" si no (nunca envía apagado)."""
        return (self.telegram_bot_token or "") if self.telegram_active else ""

    @property
    def email_active(self) -> bool:
        return self.email_enabled

    def token_hint(self) -> str | None:
        """Últimos 4 caracteres del token, para mostrar sin revelarlo."""
        token = self.telegram_bot_token or ""
        return token[-4:] if len(token) >= 8 else None

    def receives_updates(self, mode: str) -> bool:
        """¿Telegram está activo y en ese modo de respuestas?"""
        return self.telegram_active and self.telegram_updates_mode == mode

    @property
    def telegram_linkable(self) -> bool:
        """
        ¿Se puede vincular un chat? Hace falta el @usuario del bot (para el
        enlace) y que el bot lea mensajes: con el modo "off" el "/start
        <código>" nunca se procesa y el enlace no serviría.
        """
        return (
            self.telegram_active
            and bool(self.telegram_bot_username)
            and self.telegram_updates_mode != "off"
        )
