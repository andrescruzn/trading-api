# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/notifications/fund_notice_service.py
#
# PROPÓSITO:
# - Implementa FundNotifier (módulo fund): cada evento se vuelve un aviso
#   en la campana (alert_events sin regla) y, si están configurados, un
#   correo y un mensaje de Telegram al chat DE ESA PERSONA.
#
# REGLAS:
# - Nunca al chat general (TELEGRAM_DEFAULT_CHAT_ID): un aviso del fondo
#   trae montos de una persona. Sin chat vinculado, no hay Telegram.
# - Se llama después del commit del fondo; guarda la campana con su
#   propio commit y manda correo y Telegram en segundo plano.
# - Avisar nunca rompe el caso de uso: los errores se registran.
# ======================================================================

from __future__ import annotations

from html import escape
from typing import Any

from app.common.logging import get_logger
from app.common.utils import run_in_background
from app.modules.alerts.channels.fund_messages import FundNotice, fund_notice
from app.modules.alerts.channels.telegram_channel import telegram_api
from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_event_repository import AlertEventRepository
from app.modules.fund.domain.fund_notifier import FundEvent
from app.modules.mailer.domain.mail_template import FUND_NOTICE_TEMPLATE
from app.modules.users.domain.user_entity import User
from app.modules.users.domain.user_repository import UserRepository

logger = get_logger(__name__)


class FundNoticeService:

    def __init__(
        self,
        *,
        event_repo: AlertEventRepository,
        user_repo: UserRepository,
        mailer: Any | None,
        settings: Any,
        super_admin_role_id: int,
    ):
        self._event_repo = event_repo
        self._user_repo = user_repo
        self._mailer = mailer
        self._settings = settings
        self._super_admin_role_id = int(super_admin_role_id)

    def notify(self, events: list[FundEvent]) -> None:
        if not events:
            return
        try:
            deliveries = self._save(events)
        except Exception:
            self._event_repo.rollback()
            logger.exception("[Fund] No se pudieron guardar los avisos")
            return
        for user, notice in deliveries:
            try:
                self._send_email(user, notice)
                self._send_telegram(user, notice)
            except Exception:
                logger.exception("[Fund] No se pudo enviar el aviso al usuario %s", user.id)

    # ------------------------------------------------------------------

    def _save(self, events: list[FundEvent]) -> list[tuple[User, FundNotice]]:
        deliveries: list[tuple[User, FundNotice]] = []
        admins: list[User] | None = None
        for event in events:
            data = dict(event.data)
            if event.about_user_id is not None:
                about = self._user_repo.get_by_id(int(event.about_user_id))
                if about is not None:
                    data["person"] = (about.full_name or "").strip() or about.email
            notice = fund_notice(event.code, data)
            if notice is None:
                logger.warning("[Fund] Aviso sin texto: %s", event.code)
                continue
            if event.user_id is None:
                if admins is None:
                    admins = [
                        u for u in self._user_repo.list_all()
                        if u.role_id == self._super_admin_role_id
                    ]
                recipients = admins
            else:
                user = self._user_repo.get_by_id(int(event.user_id))
                recipients = [user] if user is not None else []
            for user in recipients:
                if user.status != "active":
                    continue
                self._event_repo.create(
                    AlertEvent(
                        id=0,
                        title=notice.title,
                        severity=notice.severity,
                        payload={"code": event.code, **event.data},
                        message=notice.message,
                        user_id=user.id,
                        delivery_status="sent",
                    )
                )
                deliveries.append((user, notice))
        self._event_repo.commit()
        return deliveries

    def _url(self, notice: FundNotice) -> str | None:
        base = (self._settings.FRONTEND_URL or "").rstrip("/")
        return f"{base}/#{notice.link}" if base else None

    def _send_email(self, user: User, notice: FundNotice) -> None:
        if self._mailer is None or not user.email:
            return
        self._mailer.send_by_template_in_background(
            to_email=user.email,
            template=FUND_NOTICE_TEMPLATE,
            context={
                "title": notice.title,
                "message": notice.message,
                "full_name": user.full_name,
                "url": self._url(notice),
            },
            subject_override=notice.title,
        )

    def _send_telegram(self, user: User, notice: FundNotice) -> None:
        token = self._settings.TELEGRAM_BOT_TOKEN
        if not token or user.telegram_chat_id is None:
            return
        text = f"<b>{escape(notice.title)}</b>\n{escape(notice.message)}"
        url = self._url(notice)
        payload: dict[str, Any] = {
            "chat_id": user.telegram_chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        # Telegram solo acepta botones con URL https
        if url and url.startswith("https://"):
            payload["reply_markup"] = {
                "inline_keyboard": [[{"text": "Ver en Trading App", "url": url}]]
            }
        run_in_background(telegram_api, token, "sendMessage", payload)
