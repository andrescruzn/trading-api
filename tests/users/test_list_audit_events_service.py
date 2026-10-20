# -*- coding: utf-8 -*-

# ======================================================================
# tests/users/test_list_audit_events_service.py
# ======================================================================

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.common.contracts import Page, PageRequest
from app.modules.users.services.audit import ListAuditEventsService

NOW = datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc)


def _make():
    repo = MagicMock()
    repo.list_events.side_effect = lambda filters, years, page: Page.empty(page)
    return ListAuditEventsService(repo=repo), repo


def _call_args(repo):
    filters, years, page = repo.list_events.call_args.args
    return filters, years, page


class TestListAuditEventsService:

    def test_defaults_search_current_and_previous_year(self):
        svc, repo = _make()

        result = svc.list(now=NOW)

        assert result.success
        filters, years, page = _call_args(repo)
        assert years == [2025, 2026]
        assert page == PageRequest(page=1, page_size=20)
        assert filters.date_from is None and filters.date_to is None
        assert filters.only_errors is False

    def test_date_range_selects_its_years(self):
        svc, repo = _make()

        svc.list(
            date_from=datetime(2024, 12, 1, tzinfo=timezone.utc),
            date_to=datetime(2026, 1, 1, tzinfo=timezone.utc),
            now=NOW,
        )

        _, years, _ = _call_args(repo)
        # date_to es exclusiva: el 1 de enero de 2026 a las 00:00 no entra.
        assert years == [2024, 2025]

    def test_naive_dates_are_utc(self):
        svc, repo = _make()

        svc.list(date_from=datetime(2026, 10, 1), date_to=datetime(2026, 10, 2), now=NOW)

        filters, years, _ = _call_args(repo)
        assert filters.date_from == datetime(2026, 10, 1, tzinfo=timezone.utc)
        assert filters.date_to.tzinfo == timezone.utc
        assert years == [2026]

    def test_offset_dates_are_converted_to_utc(self):
        svc, repo = _make()
        bogota = timezone(timedelta(hours=-5))

        svc.list(date_from=datetime(2026, 10, 20, 0, 0, tzinfo=bogota), now=NOW)

        filters, _, _ = _call_args(repo)
        assert filters.date_from == datetime(2026, 10, 20, 5, 0, tzinfo=timezone.utc)

    def test_invalid_range(self):
        svc, repo = _make()
        day = datetime(2026, 10, 20, tzinfo=timezone.utc)

        result = svc.list(date_from=day, date_to=day, now=NOW)

        assert result.error.code == "AUDIT_INVALID_DATE_RANGE"
        assert result.error.http_status == 422
        repo.list_events.assert_not_called()

    def test_event_type_is_normalized_and_validated(self):
        svc, repo = _make()

        assert svc.list(event_type=" verify_otp ", now=NOW).success
        assert _call_args(repo)[0].event_type == "VERIFY_OTP"

        result = svc.list(event_type="DROP_TABLE", now=NOW)
        assert result.error.code == "AUDIT_INVALID_EVENT_TYPE"

    def test_kind_is_validated(self):
        svc, repo = _make()

        assert svc.list(kind="WRITE", now=NOW).success
        assert _call_args(repo)[0].kind == "write"

        assert svc.list(kind="delete", now=NOW).error.code == "AUDIT_INVALID_KIND"

    def test_path_is_trimmed_and_limited(self):
        svc, repo = _make()

        svc.list(path="  /orders ", now=NOW)
        assert _call_args(repo)[0].path_contains == "/orders"

        svc.list(path="   ", now=NOW)
        assert _call_args(repo)[0].path_contains is None

        assert svc.list(path="x" * 201, now=NOW).error.code == "AUDIT_INVALID_PATH"

    @pytest.mark.parametrize(
        ("page", "page_size", "expected"),
        [(0, -5, PageRequest(1, 1)), (3, 500, PageRequest(3, 100)), (None, None, PageRequest(1, 20))],
    )
    def test_page_is_clamped(self, page, page_size, expected):
        svc, repo = _make()

        svc.list(page=page, page_size=page_size, now=NOW)

        assert _call_args(repo)[2] == expected

    def test_filters_are_passed_through(self):
        svc, repo = _make()

        svc.list(user_id=7, only_errors=True, now=NOW)

        filters, _, _ = _call_args(repo)
        assert filters.user_id == 7
        assert filters.only_errors is True
