# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/telegram/shared_signal_notifier.py
#
# PROPÓSITO:
# - Enviar por Telegram las señales BUY/SELL aprobadas de un agente
#   compartido (bots.share_signals) a quienes lo siguen
#   (signal_subscriptions). Lo llama GenerateSignalService como hook.
#
# NOTAS:
# - Mensaje informativo: acción, símbolo, timeframe, precios, R/R y
#   estrategia. Sin botones (quien sigue no ejecuta nada), sin tamaño de
#   posición, cuenta ni nombre del agente (no revela al dueño).
# - Nunca lanza: un fallo se loguea y se sigue con el siguiente.
# - Se omiten quienes no tienen chat vinculado y el dueño del agente (a
#   él le avisa SignalApprovalNotifier en modo Con aprobación).
# ======================================================================

from __future__ import annotations

import logging

from app.common.config.settings import Settings
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.alerts.channels.telegram_channel import telegram_api
from app.modules.alerts.channels.telegram_messages import shared_signal_text
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.domain.signal_subscription_repository import (
    SignalSubscriptionRepository,
)
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository
from app.modules.strategies.domain.strategy_repository import StrategyRepository
from app.modules.users.domain import UserRepository

logger = logging.getLogger(__name__)


class SharedSignalNotifier:
    """Reparte la señal aprobada de un agente compartido entre sus suscriptores."""

    def __init__(
        self,
        *,
        subscription_repo: SignalSubscriptionRepository,
        account_repo: AccountRepository,
        user_repo: UserRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
        strategy_repo: StrategyRepository,
        settings: Settings,
    ):
        self._subscription_repo = subscription_repo
        self._account_repo = account_repo
        self._user_repo = user_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._strategy_repo = strategy_repo
        self._settings = settings

    def notify(self, signal: Signal, bot: Bot) -> int:
        """Devuelve cuántos mensajes salieron. Nunca lanza."""
        try:
            return self._notify(signal, bot)
        except Exception:
            logger.exception("No se pudo repartir la señal compartida %s", signal.id)
            return 0

    def _notify(self, signal: Signal, bot: Bot) -> int:
        token = self._settings.TELEGRAM_BOT_TOKEN
        if not token or not bot.share_signals or not signal.is_actionable():
            return 0

        subscriptions = self._subscription_repo.list_by_bot(bot.id)
        if not subscriptions:
            return 0

        account = self._account_repo.get_by_id(bot.account_id) if bot.account_id else None
        owner_id = account.user_id if account else None

        symbol = self._symbol_repo.get_by_id(bot.symbol_id)
        timeframe = self._timeframe_repo.get_by_id(bot.timeframe_id)
        strategy = self._strategy_repo.get_by_id(bot.strategy_id)
        text = shared_signal_text(
            action=signal.action,
            symbol=symbol.symbol if symbol else "—",
            timeframe=timeframe.code if timeframe else "—",
            strategy_name=strategy.name if strategy else "—",
            entry=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            rr_ratio=signal.rr_ratio,
        )

        sent = 0
        for subscription in subscriptions:
            if subscription.user_id == owner_id:
                continue
            try:
                user = self._user_repo.get_by_id(subscription.user_id)
                if user is None or user.telegram_chat_id is None:
                    continue
                result = telegram_api(
                    token,
                    "sendMessage",
                    {"chat_id": user.telegram_chat_id, "text": text, "parse_mode": "HTML"},
                )
                if result is not None:
                    sent += 1
            except Exception:
                logger.exception(
                    "No se pudo enviar la señal compartida %s al usuario %s",
                    signal.id,
                    subscription.user_id,
                )
        return sent
