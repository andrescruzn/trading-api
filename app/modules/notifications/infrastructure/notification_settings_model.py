# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/infrastructure/notification_settings_model.py
#
# Tabla `notification_settings`: una sola fila (id = 1) con la
# configuración de los canales de notificación (antes TELEGRAM_* en .env).
# El token del bot y el secreto del webhook van cifrados con Fernet.
# ======================================================================

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, ForeignKey, String, Text, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import MYSQL_TABLE_OPTIONS, Base


class NotificationSettingsModel(Base):
    """Canales de notificación del sistema (la fila id = 1)."""

    __tablename__ = "notification_settings"
    __table_args__ = (
        CheckConstraint("`id` = 1", name="chk_notification_settings_single_row"),
        CheckConstraint(
            "`telegram_updates_mode` IN ('off', 'polling', 'webhook')",
            name="chk_notification_settings_updates_mode",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=False, comment="Siempre 1: una sola fila")
    telegram_enabled = Column(
        Boolean,
        nullable=False,
        server_default=text("'0'"),
        comment="Interruptor del canal Telegram",
    )
    telegram_bot_token_enc = Column(
        Text, nullable=True, comment="Token del bot de @BotFather, cifrado (Fernet)"
    )
    telegram_bot_username = Column(
        String(64), nullable=True, comment="@usuario del bot sin @ (lo devuelve getMe)"
    )
    telegram_default_chat_id = Column(
        String(64),
        nullable=True,
        comment="Chat de respaldo para las alertas de quien no vinculó su Telegram",
    )
    telegram_updates_mode = Column(
        String(16),
        nullable=False,
        server_default=text("'off'"),
        comment="off | polling (desarrollo) | webhook (producción)",
    )
    telegram_webhook_url = Column(
        String(2048), nullable=True, comment="URL pública https registrada con setWebhook"
    )
    telegram_webhook_secret_enc = Column(
        Text, nullable=True, comment="secret_token del webhook, cifrado (Fernet)"
    )
    email_enabled = Column(
        Boolean,
        nullable=False,
        server_default=text("'1'"),
        comment="Interruptor de los avisos por correo (no afecta el código de acceso)",
    )
    updated_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_notification_settings_updated_by", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
    )
