# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/orders/list_orders_service.py
#
# Lista órdenes de un bot. Admin ve todas las del sistema.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.order_repository import OrderRepository


class ListOrdersService:
    """
    Lista órdenes del sistema.

    Reglas de negocio:
    - Admin (owner_id=None, bot_id=None): las órdenes más recientes del sistema.
    - Usuario normal: requiere bot_id, y el bot debe ser suyo (BOT_NOT_FOUND si no).
    """

    def __init__(
        self,
        repo: OrderRepository,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
    ):
        self._repo = repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo

    def list(
        self,
        bot_id: int | None = None,
        limit: int = 100,
        owner_id: int | None = None,
    ) -> ServiceResult[list[Order]]:
        if bot_id is None:
            if owner_id is not None:
                return ServiceResult.fail(code="ORDERS_MISSING_BOT", http_status=400)
            return ServiceResult.ok(data=self._repo.list_all(limit=limit))

        if find_accessible_bot(self._bot_repo, self._account_repo, bot_id, owner_id) is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        return ServiceResult.ok(data=self._repo.list_by_bot(bot_id=bot_id, limit=limit))
