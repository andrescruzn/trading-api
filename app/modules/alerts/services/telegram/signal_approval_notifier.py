# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/telegram/signal_approval_notifier.py
#
# PROPÓSITO:
# - Avisar al dueño del agente que tiene una señal por aprobar:
#   - Telegram (si está activo y vinculó su chat): botones Aprobar /
#     Descartar (callback_data sig:a:<id> / sig:r:<id>).
#   - Correo (si está activo en Notificaciones y hay SMTP): los mismos
#     datos y un botón a la app; desde el correo no se decide.
#   Lo llama GenerateSignalService como hook.
#
# NOTAS:
# - Sin canal disponible no se envía nada: la señal igual aparece en la app.
# - El botón "Ver en Trading App" de Telegram solo se agrega con
#   FRONTEND_URL https (Telegram rechaza botones con enlaces a localhost).
# - El correo sale en segundo plano (no frena la generación de señales).
# ======================================================================

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.common.config.settings import Settings
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.alerts.channels.signal_email_messages import pending_signal_email
from app.modules.alerts.channels.telegram_channel import telegram_api
from app.modules.alerts.channels.telegram_messages import (
    BUTTON_APPROVE,
    BUTTON_OPEN_APP,
    BUTTON_REJECT,
    pending_signal_text,
)
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.signal_entity import Signal
from app.modules.mailer.domain.mail_template import NOTICE_TEMPLATE
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository
from app.modules.notifications.domain import NotificationSettings, NotificationSettingsReader
from app.modules.users.domain import UserRepository
from app.modules.users.domain.user_entity import User

if TYPE_CHECKING:
    from app.modules.mailer.services.mailer_service import MailerService

logger = logging.getLogger(__name__)


class SignalApprovalNotifier:
    """Envía la señal pendiente al dueño del agente por Telegram y correo."""

    def __init__(
        self,
        *,
        account_repo: AccountRepository,
        user_repo: UserRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
        settings: Settings,
        notification_settings: NotificationSettingsReader,
        mailer: "MailerService | None" = None,
    ):
        self._account_repo = account_repo
        self._user_repo = user_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._settings = settings
        self._notification_settings = notification_settings
        self._mailer = mailer

    def notify(self, signal: Signal, bot: Bot) -> bool:
        """True si salió por al menos un canal."""
        if bot.account_id is None:
            return False
        config = self._notification_settings.get()
        send_email = config.email_active and self._mailer is not None
        if not config.telegram_active and not send_email:
            return False

        account = self._account_repo.get_by_id(bot.account_id)
        user = self._user_repo.get_by_id(account.user_id) if account else None
        if user is None:
            return False

        symbol = self._symbol_repo.get_by_id(bot.symbol_id)
        timeframe = self._timeframe_repo.get_by_id(bot.timeframe_id)
        data = dict(
            action=signal.action,
            symbol=symbol.symbol if symbol else "—",
            timeframe=timeframe.code if timeframe else "—",
            entry=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            rr_ratio=signal.rr_ratio,
            position_size=signal.position_size,
            base_asset=symbol.base_asset if symbol else "",
            agent_name=bot.name,
            mode=bot.mode,
            expires_at=signal.expires_at,
        )

        sent = False
        if config.telegram_active and user.telegram_chat_id is not None:
            sent = self._send_telegram(config, user, signal, bot, data)
        if send_email and user.email:
            sent = self._send_email(user, bot, data) or sent
        return sent

    # ------------------------------------------------------------------

    def _agent_url(self, bot: Bot) -> str | None:
        base = (self._settings.FRONTEND_URL or "").rstrip("/")
        return f"{base}/#/agents/{bot.id}" if base else None

    def _send_telegram(
        self, config: NotificationSettings, user: User, signal: Signal, bot: Bot, data: dict
    ) -> bool:
        keyboard = [[
            {"text": BUTTON_APPROVE, "callback_data": f"sig:a:{signal.id}"},
            {"text": BUTTON_REJECT, "callback_data": f"sig:r:{signal.id}"},
        ]]
        url = self._agent_url(bot)
        if url and url.startswith("https://"):
            keyboard.append([{"text": BUTTON_OPEN_APP, "url": url}])

        return telegram_api(
            config.telegram_token,
            "sendMessage",
            {
                "chat_id": user.telegram_chat_id,
                "text": pending_signal_text(**data),
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": keyboard},
            },
        ) is not None

    def _send_email(self, user: User, bot: Bot, data: dict) -> bool:
        try:
            subject, context = pending_signal_email(**data, url=self._agent_url(bot))
            self._mailer.send_by_template_in_background(
                to_email=user.email,
                template=NOTICE_TEMPLATE,
                context={**context, "full_name": user.full_name},
                subject_override=subject,
            )
            return True
        except Exception:
            logger.exception("No se pudo encolar el correo de la señal pendiente (agente %s)", bot.id)
            return False
