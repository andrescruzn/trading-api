# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/orders/list_orders_service.py
#
# Lista órdenes de un bot. Admin ve todas las del sistema.
#
# Dos formas, con los mismos filtros y la misma regla de propiedad:
# - list():      lista simple (las `limit` más recientes). La usan las
#                pantallas que esperan un array.
# - list_page(): una página + el total (paginación en el servidor, p. ej.
#                "Todas las órdenes" del admin o la pestaña Órdenes del agente).
# ======================================================================

from __future__ import annotations

from app.common.contracts import Page, PageRequest, ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.order_repository import OrderCriteria, OrderRepository


class ListOrdersService:
    """
    Lista órdenes del sistema.

    Reglas de negocio:
    - Admin (owner_id=None, bot_id=None): las órdenes más recientes del sistema.
    - Usuario normal: requiere bot_id, y el bot debe ser suyo (BOT_NOT_FOUND si no).
    - Filtros opcionales: lado, estado, tipo y, solo para el admin, el dueño
      (`user_id`: orden → agente → cuenta → usuario). Un valor fuera del
      catálogo de la entidad → ORDERS_INVALID_FILTER (422).
    - Orden estable: la más reciente primero (ts desc, id desc).
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
        side: str | None = None,
        status: str | None = None,
        order_type: str | None = None,
        user_id: int | None = None,
    ) -> ServiceResult[list[Order]]:
        criteria = self._build_criteria(bot_id, owner_id, side, status, order_type, user_id)
        if not criteria.success:
            return ServiceResult.fail(
                code=criteria.error.code, http_status=criteria.error.http_status
            )
        return ServiceResult.ok(data=self._repo.search(criteria.data, offset=0, limit=limit))

    def list_page(
        self,
        page: PageRequest,
        bot_id: int | None = None,
        owner_id: int | None = None,
        side: str | None = None,
        status: str | None = None,
        order_type: str | None = None,
        user_id: int | None = None,
    ) -> ServiceResult[Page[Order]]:
        criteria = self._build_criteria(bot_id, owner_id, side, status, order_type, user_id)
        if not criteria.success:
            return ServiceResult.fail(
                code=criteria.error.code, http_status=criteria.error.http_status
            )
        total = self._repo.count(criteria.data)
        items = (
            self._repo.search(criteria.data, offset=page.offset, limit=page.limit)
            if total > page.offset
            else []
        )
        return ServiceResult.ok(
            data=Page(items=items, total=total, page=page.page, page_size=page.page_size)
        )

    # ------------------------------------------------------------------
    # Filtros + propiedad (comunes a las dos formas)
    # ------------------------------------------------------------------

    def _build_criteria(
        self,
        bot_id: int | None,
        owner_id: int | None,
        side: str | None,
        status: str | None,
        order_type: str | None,
        user_id: int | None,
    ) -> ServiceResult[OrderCriteria]:
        if (
            (side is not None and side not in Order.VALID_SIDES)
            or (status is not None and status not in Order.VALID_STATUSES)
            or (order_type is not None and order_type not in Order.VALID_TYPES)
        ):
            return ServiceResult.fail(code="ORDERS_INVALID_FILTER", http_status=422)

        bot_ids: list[int] | None = None
        if bot_id is None:
            if owner_id is not None:
                return ServiceResult.fail(code="ORDERS_MISSING_BOT", http_status=400)
        else:
            if find_accessible_bot(self._bot_repo, self._account_repo, bot_id, owner_id) is None:
                return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)
            bot_ids = [bot_id]

        # Filtro "Dueño" (solo admin; a un usuario ya lo acota su bot_id propio)
        if user_id is not None and owner_id is None:
            account_ids = [a.id for a in self._account_repo.list_by_user_id(user_id)]
            owned = (
                [b.id for b in self._bot_repo.list_by_account_ids(account_ids)]
                if account_ids else []
            )
            bot_ids = owned if bot_ids is None else [b for b in bot_ids if b in owned]

        return ServiceResult.ok(
            data=OrderCriteria(bot_ids=bot_ids, side=side, status=status, type=order_type)
        )
