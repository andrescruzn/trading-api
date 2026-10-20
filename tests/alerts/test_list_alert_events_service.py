# -*- coding: utf-8 -*-

# ======================================================================
# tests/alerts/test_list_alert_events_service.py
#
# Tests unitarios de ListAlertEventsService (lista simple y paginada) y de
# la paginación de SqlAlchemyAlertEventRepository (Session mockeada, sin BD).
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.common.contracts import PageRequest
from app.modules.alerts.infrastructure.alert_event_repository_impl import (
    SqlAlchemyAlertEventRepository,
)
from app.modules.alerts.services.alert_events.list_alert_events_service import (
    ListAlertEventsService,
)

SINCE = datetime(2026, 10, 1, tzinfo=timezone.utc)


def _service(total: int = 0, items: list | None = None):
    repo = MagicMock()
    repo.count.return_value = total
    repo.search.return_value = items or []
    return ListAlertEventsService(repo=repo), repo


class TestListPage:
    def test_admin_sees_all(self):
        service, repo = _service(total=250, items=["e1"])

        result = service.list_page(page=PageRequest.of(3, 50), user_id=1, is_admin=True)

        assert result.success
        assert result.data.items == ["e1"]
        assert (result.data.total, result.data.total_pages) == (250, 5)
        repo.count.assert_called_once_with(user_id=None, from_ts=None)
        repo.search.assert_called_once_with(user_id=None, from_ts=None, offset=100, limit=50)

    def test_admin_owner_filter(self):
        service, repo = _service(total=1, items=["e1"])

        service.list_page(page=PageRequest.of(1, 20), user_id=1, is_admin=True, owner_filter=9)

        repo.count.assert_called_once_with(user_id=9, from_ts=None)

    def test_user_only_sees_own_and_ignores_owner_filter(self):
        service, repo = _service(total=3)

        service.list_page(page=PageRequest.of(1, 20), user_id=7, owner_filter=9, from_ts=SINCE)

        repo.count.assert_called_once_with(user_id=7, from_ts=SINCE)

    def test_without_user_returns_empty_page(self):
        service, repo = _service()

        result = service.list_page(page=PageRequest.of(2, 20))

        assert result.success
        assert result.data.items == []
        assert (result.data.total, result.data.page) == (0, 2)
        repo.count.assert_not_called()

    def test_page_beyond_total_skips_search(self):
        service, repo = _service(total=20)

        result = service.list_page(page=PageRequest.of(2, 20), user_id=7)

        assert result.data.items == []
        repo.search.assert_not_called()


class TestList:
    def test_admin_list_applies_from_ts(self):
        service, repo = _service(items=["e1"])

        result = service.list(user_id=1, is_admin=True, limit=200, from_ts=SINCE)

        assert result.data == ["e1"]
        repo.search.assert_called_once_with(user_id=None, from_ts=SINCE, offset=0, limit=200)
        repo.count.assert_not_called()

    def test_user_list(self):
        service, repo = _service()

        service.list(user_id=7, limit=100)

        repo.search.assert_called_once_with(user_id=7, from_ts=None, offset=0, limit=100)


class TestRepositoryPagination:
    def _query(self, session: MagicMock) -> MagicMock:
        query = session.query.return_value
        for method in ("filter", "order_by", "offset", "limit"):
            getattr(query, method).return_value = query
        query.all.return_value = []
        return query

    def test_search_applies_offset_limit_and_stable_order(self):
        session = MagicMock()
        query = self._query(session)
        repo = SqlAlchemyAlertEventRepository(session)

        repo.search(user_id=7, offset=20, limit=20)

        query.offset.assert_called_once_with(20)
        query.limit.assert_called_once_with(20)
        assert len(query.order_by.call_args.args) == 2

    def test_search_without_user_does_not_filter(self):
        session = MagicMock()
        query = self._query(session)
        repo = SqlAlchemyAlertEventRepository(session)

        repo.search(limit=20)

        query.filter.assert_not_called()
        query.offset.assert_not_called()

    def test_count(self):
        session = MagicMock()
        query = self._query(session)
        query.scalar.return_value = 4
        repo = SqlAlchemyAlertEventRepository(session)

        assert repo.count(user_id=7, from_ts=SINCE) == 4
        assert query.filter.call_count == 2
