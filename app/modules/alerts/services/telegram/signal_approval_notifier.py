# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/telegram/signal_approval_notifier.py
#
# PROPÓSITO:
# - Avisar por Telegram al dueño del agente que tiene una señal por
#   aprobar, con botones Aprobar / Rechazar (callback_data sig:a:<id> /
#   sig:r:<id>). Lo llama GenerateSignalService como hook.
#
# NOTAS:
# - Sin chat vinculado no se envía nada: la señal igual aparece en la app.
# - El botón "Ver en Trading App" solo se agrega con FRONTEND_URL https
#   (Telegram rechaza botones con enlaces a localhost).
# ======================================================================

from __future__ import annotations

import logging

from app.common.config.settings import Settings
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.alerts.channels.telegram_channel import telegram_api
from app.modules.alerts.channels.telegram_messages import (
    BUTTON_APPROVE,
    BUTTON_OPEN_APP,
    BUTTON_REJECT,
    pending_signal_text,
)
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.signal_entity import Signal
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository
from app.modules.users.domain import UserRepository

logger = logging.getLogger(__name__)


class SignalApprovalNotifier:
    """Envía la señal pendiente al chat de Telegram del dueño del agente."""

    def __init__(
        self,
        *,
        account_repo: AccountRepository,
        user_repo: UserRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
        settings: Settings,
    ):
        self._account_repo = account_repo
        self._user_repo = user_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._settings = settings

    def notify(self, signal: Signal, bot: Bot) -> bool:
        if not self._settings.TELEGRAM_BOT_TOKEN or bot.account_id is None:
            return False

        account = self._account_repo.get_by_id(bot.account_id)
        user = self._user_repo.get_by_id(account.user_id) if account else None
        if user is None or user.telegram_chat_id is None:
            return False

        symbol = self._symbol_repo.get_by_id(bot.symbol_id)
        timeframe = self._timeframe_repo.get_by_id(bot.timeframe_id)

        text = pending_signal_text(
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

        keyboard = [[
            {"text": BUTTON_APPROVE, "callback_data": f"sig:a:{signal.id}"},
            {"text": BUTTON_REJECT, "callback_data": f"sig:r:{signal.id}"},
        ]]
        if self._settings.FRONTEND_URL.startswith("https://"):
            keyboard.append([{
                "text": BUTTON_OPEN_APP,
                "url": f"{self._settings.FRONTEND_URL}/#/agents/{bot.id}",
            }])

        sent = telegram_api(
            self._settings.TELEGRAM_BOT_TOKEN,
            "sendMessage",
            {
                "chat_id": user.telegram_chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": keyboard},
            },
        )
        return sent is not None
