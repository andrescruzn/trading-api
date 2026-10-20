# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/evaluation/fire_alert_service.py
#
# Crea un AlertEvent y despacha la notificación a todos los canales
# activos de la regla (fire-and-forget).
#
# DISEÑO:
# - El disparo es fire-and-forget: si un canal falla, se registra
#   el fallo pero NO se aborta la operación de negocio que lo disparó.
# - El AlertEvent se persiste siempre (con delivery_status según resultado).
#
# DESTINATARIO (dueño de la regla, `rule.user_id`):
# - Telegram: el chat que el dueño vinculó (`users.telegram_chat_id`); si
#   no vinculó ninguno, el chat del sistema (TELEGRAM_DEFAULT_CHAT_ID).
# - Email: el correo del request (si lo hay) o el del dueño. Así las
#   alertas de hooks y del scheduler, que no tienen request, también llegan.
# - Si no se puede leer el dueño, se usan los valores por defecto: el
#   despacho nunca lanza.
# ======================================================================

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_event_repository import AlertEventRepository
from app.modules.alerts.domain.alert_rule_entity import AlertRule

if TYPE_CHECKING:
    from app.common.config.settings import Settings
    from app.modules.mailer.services.mailer_service import MailerService
    from app.modules.users.domain import User, UserRepository

logger = logging.getLogger(__name__)


class FireAlertService:
    """
    Crea y despacha un AlertEvent a todos los canales activos de la regla.
    """

    def __init__(
        self,
        event_repo: AlertEventRepository,
        settings: "Settings",
        mailer: "MailerService | None" = None,
        user_email: str | None = None,
        user_repo: "UserRepository | None" = None,
    ):
        self._event_repo = event_repo
        self._settings = settings
        self._mailer = mailer
        self._user_email = user_email
        self._user_repo = user_repo

    def fire(
        self,
        rule: AlertRule,
        title: str,
        severity: str = "info",
        message: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AlertEvent:
        """
        Crea el AlertEvent en BD y lo despacha a los canales configurados.

        Retorna el evento creado (con delivery_status actualizado).
        """
        event = AlertEvent(
            id=0,
            title=title,
            severity=severity,
            payload=payload or {},
            delivery_status="pending",
            message=message,
            alert_rule_id=rule.id,
            user_id=rule.user_id,
            bot_id=rule.bot_id,
        )

        # Persistir antes de despachar (para tener event.id si los canales lo necesitan)
        event = self._event_repo.create(event)

        # Despachar a todos los canales activos
        channels = self._build_channels(rule)
        all_ok = True

        for channel in channels:
            try:
                ok = channel.send(event, rule)
                if not ok:
                    all_ok = False
            except Exception as exc:
                logger.error("Channel %s raised: %s", type(channel).__name__, exc)
                all_ok = False

        # Actualizar estado de entrega
        if channels:
            if all_ok:
                event.mark_sent()
            else:
                event.mark_failed()
            self._event_repo.update(event)

        self._event_repo.commit()
        return event

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_channels(self, rule: AlertRule) -> list:
        from app.modules.alerts.channels.email_channel import EmailChannel
        from app.modules.alerts.channels.telegram_channel import TelegramChannel
        from app.modules.alerts.channels.webhook_channel import WebhookChannel
        from app.modules.alerts.channels.desktop_channel import DesktopChannel

        channels: list = []
        needs_owner = rule.wants_telegram() or (rule.wants_email() and not self._user_email)
        owner = self._owner(rule) if needs_owner else None

        to_email = self._user_email or (owner.email if owner else None)
        if rule.wants_email() and self._mailer and to_email:
            channels.append(EmailChannel(mailer=self._mailer, to_email=to_email))

        if rule.wants_telegram():
            # Sin chat vinculado, TelegramChannel usa TELEGRAM_DEFAULT_CHAT_ID
            chat_id = owner.telegram_chat_id if owner else None
            channels.append(TelegramChannel(settings=self._settings, chat_id=chat_id))

        webhook_url = rule.wants_webhook()
        if webhook_url:
            channels.append(WebhookChannel(url=webhook_url))

        if rule.wants_desktop() and self._settings.DESKTOP_NOTIFICATIONS_ENABLED:
            channels.append(DesktopChannel())

        return channels

    def _owner(self, rule: AlertRule) -> "User | None":
        if self._user_repo is None or rule.user_id is None:
            return None
        try:
            return self._user_repo.get_by_id(rule.user_id)
        except Exception:
            logger.exception("FireAlertService: no se pudo leer el dueño de la regla %s", rule.id)
            return None
