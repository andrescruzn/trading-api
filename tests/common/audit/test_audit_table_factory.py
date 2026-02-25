# -*- coding: utf-8 -*-

# ======================================================================
# tests/common/audit/test_audit_table_factory.py
#
# Tests unitarios para audit_table_factory.py.
# Engine mockeado — sin I/O real a BD.
# ======================================================================

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from app.common.audit import audit_table_factory
from app.common.audit.audit_table_factory import get_or_create_table


# ======================================================================
# Fixture: engine mock
# ======================================================================

@pytest.fixture
def mock_engine():
    """Engine falso que simula begin() como context manager."""
    engine = MagicMock()
    conn = MagicMock()

    @contextmanager
    def fake_begin():
        yield conn

    engine.begin = fake_begin
    return engine, conn


@pytest.fixture(autouse=True)
def clear_table_cache():
    """Limpia el caché entre tests para evitar interferencias."""
    audit_table_factory._table_cache.clear()
    yield
    audit_table_factory._table_cache.clear()


# ======================================================================
# Tests
# ======================================================================

class TestGetOrCreateTable:

    def test_returns_table_object(self, mock_engine):
        engine, _ = mock_engine
        table = get_or_create_table(year=2099, engine=engine)
        assert table is not None
        assert table.name == "http_audit_2099"

    def test_table_has_required_columns(self, mock_engine):
        engine, _ = mock_engine
        table = get_or_create_table(year=2099, engine=engine)
        column_names = {c.name for c in table.columns}
        required = {
            "id", "user_id", "event_type", "method", "path",
            "status_code", "ip", "user_agent", "referer",
            "request_payload", "response_payload", "duration_ms", "ts",
        }
        assert required.issubset(column_names)

    def test_create_called_first_time(self, mock_engine):
        """Verifica que engine.begin() se invocó al crear la tabla por primera vez."""
        engine, conn = mock_engine
        # Wrapeamos engine.begin para rastrear llamadas
        original_begin = engine.begin
        called = []

        from contextlib import contextmanager

        @contextmanager
        def tracked_begin():
            called.append(True)
            with original_begin():
                yield conn

        engine.begin = tracked_begin
        get_or_create_table(year=2099, engine=engine)
        assert len(called) == 1, "engine.begin() debe haberse llamado una vez para CREATE TABLE"

    def test_second_call_uses_cache(self, mock_engine):
        engine, conn = mock_engine
        t1 = get_or_create_table(year=2099, engine=engine)
        # Reset the mock call count
        conn.execute.reset_mock()

        t2 = get_or_create_table(year=2099, engine=engine)

        # Same object from cache
        assert t1 is t2
        # No DB call on second access
        conn.execute.assert_not_called()

    def test_different_years_create_different_tables(self, mock_engine):
        engine, _ = mock_engine
        t2026 = get_or_create_table(year=2026, engine=engine)
        t2027 = get_or_create_table(year=2027, engine=engine)
        assert t2026.name == "http_audit_2026"
        assert t2027.name == "http_audit_2027"
        assert t2026 is not t2027
