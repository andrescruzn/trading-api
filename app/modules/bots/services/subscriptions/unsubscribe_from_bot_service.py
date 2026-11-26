# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/subscriptions/unsubscribe_from_bot_service.py
#
# PROPÓSITO:
# - Un usuario deja de seguir las señales de un agente.
#
# DECISIONES:
# - Si la suscripción existe se borra aunque el dueño haya dejado de
#   compartir: quien la tiene ya conoce el agente y debe poder salir.
# - Sin suscripción: agente compartido → ok (idempotente); inexistente o
#   privado → BOT_NOT_FOUND (no revela agentes privados).
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.domain.signal_subscription_repository import (
    SignalSubscriptionRepository,
)
from app.modules.bots.services.subscriptions.subscribe_to_bot_service import SubscriptionState


class UnsubscribeFromBotService:
    """Borra la suscripción de un usuario a un agente."""

    def __init__(
        self,
        bot_repo: BotRepository,
        subscription_repo: SignalSubscriptionRepository,
    ):
        self._bot_repo = bot_repo
        self._subscription_repo = subscription_repo

    def unsubscribe(self, bot_id: int, user_id: int) -> ServiceResult[SubscriptionState]:
        if self._subscription_repo.exists(bot_id, user_id):
            self._subscription_repo.delete(bot_id, user_id)
            self._subscription_repo.commit()
        else:
            bot = self._bot_repo.get_by_id(bot_id)
            if bot is None or not bot.share_signals:
                return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        count = self._subscription_repo.count_by_bot_ids([bot_id]).get(bot_id, 0)
        return ServiceResult.ok(
            data=SubscriptionState(bot_id=bot_id, is_subscribed=False, subscribers_count=count)
        )
