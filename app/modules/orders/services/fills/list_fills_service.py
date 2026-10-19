# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/fills/list_fills_service.py
#
# Lista los fills de una orden o de un bot completo.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.domain.fill_repository import FillRepository
from app.modules.orders.domain.order_repository import OrderRepository


class ListFillsService:
    """
    Lista fills del sistema.

    Reglas de negocio:
    - Si se pasa order_id: retorna todos los fills de esa orden.
    - Si se pasa bot_id: retorna los fills recientes de ese bot (via JOIN).
    - Al menos uno de los dos debe estar presente.
    - Propiedad: el bot (directo o el de la orden) debe ser del usuario;
      si no, se responde como si no existiera.
    """

    def __init__(
        self,
        fill_repo: FillRepository,
        order_repo: OrderRepository,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
    ):
        self._fill_repo = fill_repo
        self._order_repo = order_repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo

    def list(
        self,
        order_id: int | None = None,
        bot_id: int | None = None,
        limit: int = 200,
        owner_id: int | None = None,
    ) -> ServiceResult[list[Fill]]:
        if order_id is None and bot_id is None:
            return ServiceResult.fail(
                code="FILLS_MISSING_FILTER",
                http_status=422,
            )

        if order_id is not None:
            # Verificar que la orden exista y sea del usuario antes de listar fills
            order = self._order_repo.get_by_id(order_id)
            if order is None or not self._can_access(order.bot_id, owner_id):
                return ServiceResult.fail(code="ORDER_NOT_FOUND", http_status=404)
            fills = self._fill_repo.list_by_order(order_id=order_id)
        else:
            if not self._can_access(bot_id, owner_id):
                return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)
            fills = self._fill_repo.list_by_bot(bot_id=bot_id, limit=limit)

        return ServiceResult.ok(data=fills)

    def _can_access(self, bot_id: int, owner_id: int | None) -> bool:
        return find_accessible_bot(self._bot_repo, self._account_repo, bot_id, owner_id) is not None
