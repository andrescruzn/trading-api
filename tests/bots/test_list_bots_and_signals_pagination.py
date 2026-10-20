# -*- coding: utf-8 -*-

# ======================================================================
# tests/bots/test_list_bots_and_signals_pagination.py
#
# Tests unitarios de la paginación en el servidor de M7:
# - ListBotsService (lista simple y paginada, filtros y dueño).
# - ListSignalsService.list_page.
# - SqlAlchemyBotRepository / SqlAlchemySignalRepository con Session mockeada.
#
# ESTRATEGIA: repositorios MagicMock; cuentas y bots con SimpleNamespace.
# ======================================================================

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.common.contracts import PageRequest
from app.modules.bots.domain.bot_repository import BotCriteria
from app.modules.bots.infrastructure.bot_repository_impl import SqlAlchemyBotRepository
from app.modules.bots.infrastructure.signal_repository_impl import SqlAlchemySignalRepository
from app.modules.bots.services.bots.list_bots_service import ListBotsService
from app.modules.bots.services.signals.list_signals_service import ListSignalsService


def _accounts(*ids: int) -> list[SimpleNamespace]:
    return [SimpleNamespace(id=i) for i in ids]


def _chainable_query(session: MagicMock) -> MagicMock:
    query = session.query.return_value
    for method in ("filter", "order_by", "offset", "limit"):
        getattr(query, method).return_value = query
    query.all.return_value = []
    return query


# ======================================================================
# ListBotsService
# ======================================================================

def _bots_service(total: int = 0, items: list | None = None, accounts_by_user: dict | None = None):
    repo = MagicMock()
    repo.count.return_value = total
    repo.search.return_value = items or []
    account_repo = MagicMock()
    accounts_by_user = accounts_by_user or {}
    account_repo.list_by_user_id.side_effect = lambda uid: accounts_by_user.get(uid, [])
    return ListBotsService(repo=repo, account_repo=account_repo), repo


class TestListBotsPage:
    def test_admin_page_with_filters(self):
        service, repo = _bots_service(total=30, items=["b1"])

        result = service.list_page(page=PageRequest.of(2, 10), status="running", mode="paper")

        assert result.success
        assert result.data.items == ["b1"]
        assert (result.data.total, result.data.total_pages) == (30, 3)
        criteria = BotCriteria(account_ids=None, status="running", mode="paper")
        repo.count.assert_called_once_with(criteria)
        repo.search.assert_called_once_with(criteria, offset=10, limit=10)

    def test_admin_owner_filter_uses_owner_accounts(self):
        service, repo = _bots_service(total=1, accounts_by_user={9: _accounts(3, 4)})

        service.list_page(page=PageRequest.of(1, 20), user_id=9)

        assert repo.count.call_args.args[0].account_ids == [3, 4]

    def test_admin_owner_and_account_must_match(self):
        service, repo = _bots_service(accounts_by_user={9: _accounts(3)})

        service.list_page(page=PageRequest.of(1, 20), user_id=9, account_id=8)

        assert repo.count.call_args.args[0].account_ids == []

    def test_user_scope_wins_over_owner_filter(self):
        service, repo = _bots_service(accounts_by_user={7: _accounts(1), 9: _accounts(3)})

        service.list_page(page=PageRequest.of(1, 20), owner_id=7, user_id=9)

        assert repo.count.call_args.args[0].account_ids == [1]

    def test_page_beyond_total_skips_search(self):
        service, repo = _bots_service(total=5)

        result = service.list_page(page=PageRequest.of(3, 20))

        assert result.data.items == []
        repo.search.assert_not_called()

    def test_invalid_filter(self):
        service, repo = _bots_service()

        result = service.list_page(page=PageRequest.of(1, 20), mode="demo")

        assert not result.success
        assert result.error.code == "BOTS_INVALID_FILTER"
        assert result.error.http_status == 422
        repo.count.assert_not_called()


class TestListBotsSimple:
    def test_admin_list_has_no_limit(self):
        service, repo = _bots_service(items=["b1", "b2"])

        result = service.list()

        assert result.data == ["b1", "b2"]
        repo.search.assert_called_once_with(BotCriteria())
        repo.count.assert_not_called()

    def test_user_with_foreign_account_gets_nothing(self):
        service, repo = _bots_service(accounts_by_user={7: _accounts(1)})

        service.list(account_id=5, owner_id=7)

        repo.search.assert_called_once_with(BotCriteria(account_ids=[]))


# ======================================================================
# ListSignalsService.list_page
# ======================================================================

def _signals_service(total: int = 0, bot_account_user: int | None = 7):
    repo = MagicMock()
    repo.count_by_bot.return_value = total
    repo.list_by_bot.return_value = ["s1"]
    bot_repo = MagicMock()
    bot_repo.get_by_id.return_value = (
        SimpleNamespace(id=1, account_id=2) if bot_account_user is not None else None
    )
    account_repo = MagicMock()
    account_repo.get_by_id.return_value = SimpleNamespace(id=2, user_id=bot_account_user)
    return ListSignalsService(repo=repo, bot_repo=bot_repo, account_repo=account_repo), repo


class TestListSignalsPage:
    def test_page_counts_and_slices(self):
        service, repo = _signals_service(total=96)

        result = service.list_page(bot_id=1, page=PageRequest.of(2, 20), owner_id=7)

        assert result.success
        assert result.data.items == ["s1"]
        assert (result.data.total, result.data.total_pages) == (96, 5)
        repo.count_by_bot.assert_called_once_with(bot_id=1, action=None, from_ts=None, to_ts=None)
        repo.list_by_bot.assert_called_once_with(
            bot_id=1, action=None, from_ts=None, to_ts=None, limit=20, offset=20
        )

    def test_foreign_bot_gets_404(self):
        service, repo = _signals_service(bot_account_user=8)

        result = service.list_page(bot_id=1, page=PageRequest.of(1, 20), owner_id=7)

        assert result.error.code == "BOT_NOT_FOUND"
        repo.count_by_bot.assert_not_called()

    def test_invalid_action(self):
        service, _ = _signals_service()

        result = service.list_page(bot_id=1, page=PageRequest.of(1, 20), action="short")

        assert result.error.code == "SIGNAL_INVALID_ACTION_FILTER"

    def test_empty_page_skips_list(self):
        service, repo = _signals_service(total=0)

        result = service.list_page(bot_id=1, page=PageRequest.of(1, 20))

        assert result.data.items == []
        repo.list_by_bot.assert_not_called()


# ======================================================================
# Repositorios SQL (Session mockeada)
# ======================================================================

class TestBotRepositoryPagination:
    def test_empty_account_ids_does_not_query(self):
        session = MagicMock()
        repo = SqlAlchemyBotRepository(session)

        assert repo.search(BotCriteria(account_ids=[])) == []
        assert repo.count(BotCriteria(account_ids=[])) == 0
        session.query.assert_not_called()

    def test_search_without_limit_skips_offset_and_limit(self):
        session = MagicMock()
        query = _chainable_query(session)
        repo = SqlAlchemyBotRepository(session)

        repo.search(BotCriteria())

        query.offset.assert_not_called()
        query.limit.assert_not_called()

    def test_search_page(self):
        session = MagicMock()
        query = _chainable_query(session)
        repo = SqlAlchemyBotRepository(session)

        repo.search(BotCriteria(status="running"), offset=20, limit=10)

        query.offset.assert_called_once_with(20)
        query.limit.assert_called_once_with(10)
        assert len(query.order_by.call_args.args) == 2


class TestSignalRepositoryPagination:
    def test_list_by_bot_applies_offset(self):
        session = MagicMock()
        query = _chainable_query(session)
        repo = SqlAlchemySignalRepository(session)

        repo.list_by_bot(bot_id=1, limit=20, offset=40)

        query.offset.assert_called_once_with(40)
        query.limit.assert_called_once_with(20)

    def test_list_by_bot_first_page_has_no_offset(self):
        session = MagicMock()
        query = _chainable_query(session)
        repo = SqlAlchemySignalRepository(session)

        repo.list_by_bot(bot_id=1, limit=5000)

        query.offset.assert_not_called()
        query.limit.assert_called_once_with(500)

    def test_count_by_bot(self):
        session = MagicMock()
        query = _chainable_query(session)
        query.scalar.return_value = 12
        repo = SqlAlchemySignalRepository(session)

        assert repo.count_by_bot(bot_id=1, action="buy") == 12
