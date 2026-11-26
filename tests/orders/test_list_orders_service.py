# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_list_orders_service.py
#
# Tests unitarios de ListOrdersService (lista simple y paginada) y de la
# paginación de SqlAlchemyOrderRepository.
#
# ESTRATEGIA:
# - OrderRepository, BotRepository y AccountRepository son MagicMock.
# - Cuentas y bots se simulan con SimpleNamespace (solo id/user_id/account_id).
# - El repositorio SQL se prueba con una Session mockeada: sin BD.
# ======================================================================

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.common.config import settings
from app.common.contracts import Page, PageRequest, ServiceResult
from app.modules.orders.domain.order_repository import OrderCriteria
from app.modules.orders.infrastructure.order_repository_impl import SqlAlchemyOrderRepository
from app.modules.orders.rest.orders.routes import list_orders
from app.modules.orders.services.orders.list_orders_service import ListOrdersService


# ======================================================================
# Helpers
# ======================================================================

def _make_service(
    total: int = 0,
    items: list | None = None,
    bot: SimpleNamespace | None = None,
    account_user_id: int = 7,
    user_accounts: list | None = None,
    account_bots: list | None = None,
) -> tuple[ListOrdersService, MagicMock, MagicMock, MagicMock]:
    repo = MagicMock()
    repo.count.return_value = total
    repo.search.return_value = items or []

    bot_repo = MagicMock()
    bot_repo.get_by_id.return_value = bot
    bot_repo.list_by_account_ids.return_value = account_bots or []

    account_repo = MagicMock()
    account_repo.get_by_id.return_value = SimpleNamespace(id=2, user_id=account_user_id)
    account_repo.list_by_user_id.return_value = user_accounts or []

    service = ListOrdersService(repo=repo, bot_repo=bot_repo, account_repo=account_repo)
    return service, repo, bot_repo, account_repo


def _bot(bot_id: int = 1, account_id: int = 2) -> SimpleNamespace:
    return SimpleNamespace(id=bot_id, account_id=account_id)


# ======================================================================
# list_page
# ======================================================================

class TestListPage:
    def test_admin_without_filters_counts_and_slices(self):
        service, repo, _, _ = _make_service(total=45, items=["o1", "o2"])

        result = service.list_page(page=PageRequest.of(3, 20))

        assert result.success
        assert result.data.items == ["o1", "o2"]
        assert (result.data.total, result.data.page, result.data.page_size) == (45, 3, 20)
        assert result.data.total_pages == 3
        criteria = repo.count.call_args.args[0]
        assert criteria == OrderCriteria()
        repo.search.assert_called_once_with(criteria, offset=40, limit=20)

    def test_page_beyond_total_skips_search(self):
        service, repo, _, _ = _make_service(total=10)

        result = service.list_page(page=PageRequest.of(2, 10))

        assert result.success
        assert result.data.items == []
        assert result.data.total == 10
        repo.search.assert_not_called()

    def test_filters_reach_the_repository(self):
        service, repo, _, _ = _make_service(total=1, items=["o"])

        service.list_page(
            page=PageRequest.of(1, 20), side="buy", status="filled", order_type="market"
        )

        assert repo.count.call_args.args[0] == OrderCriteria(
            bot_ids=None, side="buy", status="filled", type="market"
        )

    def test_owner_filter_resolves_bots_of_user_accounts(self):
        service, repo, bot_repo, account_repo = _make_service(
            total=3,
            user_accounts=[SimpleNamespace(id=11), SimpleNamespace(id=12)],
            account_bots=[_bot(5), _bot(6)],
        )

        service.list_page(page=PageRequest.of(1, 20), user_id=9)

        account_repo.list_by_user_id.assert_called_once_with(9)
        bot_repo.list_by_account_ids.assert_called_once_with([11, 12])
        assert repo.count.call_args.args[0].bot_ids == [5, 6]

    def test_owner_without_accounts_yields_empty_criteria(self):
        service, repo, bot_repo, _ = _make_service(total=0, user_accounts=[])

        result = service.list_page(page=PageRequest.of(1, 20), user_id=9)

        assert result.success
        assert result.data.total == 0
        bot_repo.list_by_account_ids.assert_not_called()
        assert repo.count.call_args.args[0].bot_ids == []

    def test_owner_filter_intersects_with_bot_id(self):
        service, repo, _, _ = _make_service(
            bot=_bot(5),
            user_accounts=[SimpleNamespace(id=11)],
            account_bots=[_bot(6)],
        )

        service.list_page(page=PageRequest.of(1, 20), bot_id=5, user_id=9)

        # El agente 5 no es del dueño 9: ninguna orden
        assert repo.count.call_args.args[0].bot_ids == []

    def test_user_needs_bot_id(self):
        service, repo, _, _ = _make_service()

        result = service.list_page(page=PageRequest.of(1, 20), owner_id=7)

        assert not result.success
        assert result.error.code == "ORDERS_MISSING_BOT"
        assert result.error.http_status == 400
        repo.count.assert_not_called()

    def test_user_with_own_bot_ignores_owner_filter(self):
        service, repo, _, account_repo = _make_service(total=2, bot=_bot(5), account_user_id=7)

        result = service.list_page(page=PageRequest.of(1, 20), bot_id=5, owner_id=7, user_id=99)

        assert result.success
        assert repo.count.call_args.args[0].bot_ids == [5]
        account_repo.list_by_user_id.assert_not_called()

    def test_user_with_foreign_bot_gets_404(self):
        service, repo, _, _ = _make_service(bot=_bot(5), account_user_id=8)

        result = service.list_page(page=PageRequest.of(1, 20), bot_id=5, owner_id=7)

        assert not result.success
        assert result.error.code == "BOT_NOT_FOUND"
        assert result.error.http_status == 404
        repo.count.assert_not_called()

    def test_invalid_filter_value(self):
        service, repo, _, _ = _make_service()

        result = service.list_page(page=PageRequest.of(1, 20), status="lost")

        assert not result.success
        assert result.error.code == "ORDERS_INVALID_FILTER"
        assert result.error.http_status == 422
        repo.count.assert_not_called()


# ======================================================================
# list (lista simple, compatibilidad)
# ======================================================================

class TestList:
    def test_admin_list_uses_limit_without_count(self):
        service, repo, _, _ = _make_service(items=["o1"])

        result = service.list(limit=500)

        assert result.success
        assert result.data == ["o1"]
        repo.search.assert_called_once_with(OrderCriteria(), offset=0, limit=500)
        repo.count.assert_not_called()

    def test_user_list_by_own_bot(self):
        service, repo, _, _ = _make_service(items=["o1"], bot=_bot(5), account_user_id=7)

        result = service.list(bot_id=5, limit=100, owner_id=7)

        assert result.success
        repo.search.assert_called_once_with(OrderCriteria(bot_ids=[5]), offset=0, limit=100)

    def test_user_list_without_bot_fails(self):
        service, _, _, _ = _make_service()

        result = service.list(owner_id=7)

        assert result.error.code == "ORDERS_MISSING_BOT"


# ======================================================================
# SqlAlchemyOrderRepository: paginación
# ======================================================================

class TestOrderRepositoryPagination:
    def test_empty_bot_ids_does_not_query(self):
        session = MagicMock()
        repo = SqlAlchemyOrderRepository(session)

        assert repo.search(OrderCriteria(bot_ids=[]), offset=0, limit=20) == []
        assert repo.count(OrderCriteria(bot_ids=[])) == 0
        session.query.assert_not_called()

    def test_search_applies_offset_and_limit(self):
        session = MagicMock()
        query = session.query.return_value
        for method in ("filter", "order_by", "offset", "limit"):
            getattr(query, method).return_value = query
        query.all.return_value = []
        repo = SqlAlchemyOrderRepository(session)

        repo.search(OrderCriteria(side="buy"), offset=40, limit=20)

        query.offset.assert_called_once_with(40)
        query.limit.assert_called_once_with(20)
        # Orden estable: ts desc + id desc
        assert len(query.order_by.call_args.args) == 2

    def test_count_returns_int(self):
        session = MagicMock()
        query = session.query.return_value
        query.filter.return_value = query
        query.scalar.return_value = 17
        repo = SqlAlchemyOrderRepository(session)

        assert repo.count(OrderCriteria(status="filled")) == 17


# ======================================================================
# GET /orders: contrato con y sin `page` (la función de la ruta, sin HTTP)
# ======================================================================

def _call_list_orders_route(factory: MagicMock, page: int | None, role_id: int) -> dict:
    response = list_orders(
        bot_id=None, limit=500, side="buy", status=None, order_type=None, user_id=9,
        page=page, page_size=20,
        identity={"user_id": 1, "role_id": role_id}, factory=factory,
    )
    return json.loads(response.body)


class TestListOrdersRouteContract:
    def _admin_role(self) -> int:
        return int(settings.AUTH_SUPER_ADMIN_ROLE_ID)

    def test_without_page_returns_plain_list(self):
        factory = MagicMock()
        factory.list_orders.return_value.list.return_value = ServiceResult.ok(data=[])

        body = _call_list_orders_route(factory, page=None, role_id=self._admin_role())

        assert body["errorCode"] == 200
        assert body["data"] == []
        kwargs = factory.list_orders.return_value.list.call_args.kwargs
        assert (kwargs["limit"], kwargs["side"], kwargs["user_id"], kwargs["owner_id"]) == (
            500, "buy", 9, None,
        )

    def test_with_page_returns_items_and_pagination(self):
        factory = MagicMock()
        factory.list_orders.return_value.list_page.return_value = ServiceResult.ok(
            data=Page(items=[], total=41, page=2, page_size=20)
        )

        body = _call_list_orders_route(factory, page=2, role_id=self._admin_role())

        assert body["errorCode"] == 200
        assert body["data"] == {
            "items": [],
            "pagination": {"total": 41, "page": 2, "page_size": 20, "total_pages": 3},
        }
        request = factory.list_orders.return_value.list_page.call_args.kwargs["page"]
        assert (request.page, request.page_size) == (2, 20)

    def test_with_page_maps_service_errors(self):
        factory = MagicMock()
        factory.list_orders.return_value.list_page.return_value = ServiceResult.fail(
            code="ORDERS_MISSING_BOT", http_status=400
        )

        body = _call_list_orders_route(factory, page=1, role_id=-1)

        assert body["errorCode"] == 400
        assert body["msg"] == "Elige un agente para ver sus órdenes."
