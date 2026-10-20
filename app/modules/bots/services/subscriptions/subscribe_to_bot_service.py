# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/subscriptions/subscribe_to_bot_service.py
#
# PROPÓSITO:
# - Un usuario empieza a seguir las señales de un agente compartido.
#
# DECISIONES:
# - Idempotente: si ya lo sigue, responde ok sin crear otra fila (un doble
#   clic no es un error para la persona).
# - Agente inexistente o que no comparte → BOT_NOT_FOUND (404): no se
#   revela qué agentes privados existen.
# - Exige Telegram vinculado: es el único canal por el que llegan.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.domain.signal_subscription_entity import SignalSubscription
from app.modules.bots.domain.signal_subscription_repository import (
    SignalSubscriptionRepository,
)
from app.modules.bots.services.bots.bot_access import bot_owner_id
from app.modules.users.domain import UserRepository


@dataclass(frozen=True)
class SubscriptionState:
    """Estado de la suscripción tras suscribirse o dejar de seguir."""

    bot_id: int
    is_subscribed: bool
    subscribers_count: int


class SubscribeToBotService:
    """
    Suscribe a un usuario a las señales de un agente compartido.

    Reglas de negocio:
    - Solo agentes con share_signals = True.
    - Nadie sigue su propio agente (SUBSCRIPTION_OWN_BOT).
    - Hace falta Telegram vinculado (SUBSCRIPTION_TELEGRAM_REQUIRED).
    """

    def __init__(
        self,
        bot_repo: BotRepository,
        subscription_repo: SignalSubscriptionRepository,
        account_repo: AccountRepository,
        user_repo: UserRepository,
    ):
        self._bot_repo = bot_repo
        self._subscription_repo = subscription_repo
        self._account_repo = account_repo
        self._user_repo = user_repo

    def subscribe(self, bot_id: int, user_id: int) -> ServiceResult[SubscriptionState]:
        bot = self._bot_repo.get_by_id(bot_id)
        if bot is None or not bot.share_signals:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        if bot_owner_id(self._account_repo, bot) == user_id:
            return ServiceResult.fail(code="SUBSCRIPTION_OWN_BOT", http_status=422)

        if not self._subscription_repo.exists(bot_id, user_id):
            user = self._user_repo.get_by_id(user_id)
            if user is None or user.telegram_chat_id is None:
                return ServiceResult.fail(code="SUBSCRIPTION_TELEGRAM_REQUIRED", http_status=422)

            self._subscription_repo.create(
                SignalSubscription(id=0, bot_id=bot_id, user_id=user_id)
            )
            self._subscription_repo.commit()

        count = self._subscription_repo.count_by_bot_ids([bot_id]).get(bot_id, 0)
        return ServiceResult.ok(
            data=SubscriptionState(bot_id=bot_id, is_subscribed=True, subscribers_count=count)
        )
