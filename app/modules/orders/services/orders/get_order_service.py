# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/orders/get_order_service.py
#
# Obtiene el detalle de una orden por ID.
#
# NOTAS:
# - Propiedad: la orden pertenece al dueño del bot (bot → cuenta → user).
#   Una orden de un bot ajeno se trata como inexistente (ORDER_NOT_FOUND).
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.order_repository import OrderRepository


class GetOrderService:
    """Retorna el detalle de una orden por su ID (solo si el bot es del usuario)."""

    def __init__(
        self,
        repo: OrderRepository,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
    ):
        self._repo = repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo

    def get(self, order_id: int, owner_id: int | None = None) -> ServiceResult[Order]:
        order = self._repo.get_by_id(order_id)
        if order is None:
            return ServiceResult.fail(code="ORDER_NOT_FOUND", http_status=404)

        if find_accessible_bot(self._bot_repo, self._account_repo, order.bot_id, owner_id) is None:
            return ServiceResult.fail(code="ORDER_NOT_FOUND", http_status=404)

        return ServiceResult.ok(data=order)
