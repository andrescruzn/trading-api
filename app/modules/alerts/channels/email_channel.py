# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/email_channel.py
#
# Canal de notificación via Email (usa MailerService existente).
# ======================================================================

from __future__ import annotations

import logging

from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_rule_entity import AlertRule
from app.modules.mailer.services.mailer_service import MailerService
from app.modules.mailer.domain.mail_template import ALERT_TEMPLATE

logger = logging.getLogger(__name__)


class EmailChannel:
    """
    Canal Email — usa MailerService con template alert.html.

    Si el usuario tiene email en rule.user_id, lo resuelve desde el payload.
    Como alternativa, el payload puede incluir 'to_email' directamente.
    """

    def __init__(self, mailer: MailerService, to_email: str):
        self._mailer = mailer
        self._to_email = to_email

    def send(self, event: AlertEvent, rule: AlertRule) -> bool:
        try:
            result = self._mailer.send_by_template(
                to_email=self._to_email,
                template=ALERT_TEMPLATE,
                context={
                    "title": event.title,
                    "message": event.message or "",
                    "severity": event.severity,
                    "rule_name": rule.name,
                    "payload": event.payload,
                },
                subject_override=f"[{event.severity.upper()}] {event.title}",
            )
            if not result.success:
                logger.warning("EmailChannel failed: %s", result.error)
                return False
            return True
        except Exception as exc:
            logger.error("EmailChannel exception: %s", exc)
            return False
