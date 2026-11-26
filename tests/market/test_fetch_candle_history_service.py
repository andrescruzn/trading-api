# -*- coding: utf-8 -*-

# ======================================================================
# tests/market/test_fetch_candle_history_service.py
#
# FetchCandleHistoryService (historia para el backtesting de M5): pide
# por páginas desde `ahora − bars × timeframe`, quita la vela en
# formación, devuelve como mucho `bars` velas y nunca guarda nada.
# Complementa los dos casos de tests/strategies/test_backtest.py.
# Sin red: cliente ccxt falso inyectado con `client_factory`.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import ccxt
import pytest

from app.modules.market.services.candles import FetchCandleHistoryService
from app.modules.market.services.candles import fetch_candle_history_service as history_module

STEP = 3_600_000  # 1h en ms


def _rows(start_index: int, n: int, override: dict[int, list] | None = None) -> list[list]:
    """Filas ccxt [ts_ms, o, h, l, c, v] para las horas start_index…; `override` cambia algunas."""
    override = override or {}
    return [
        override.get(i, [i * STEP, 100, 101, 99, 100, 5])
        for i in range(start_index, start_index + n)
    ]


def _make(monkeypatch, pages=None, now_ms=10 * STEP + STEP // 2, symbol=True, timeframe=True,
          exchange="Binance", error=None):
    monkeypatch.setattr(
        history_module, "utc_now", lambda: datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc)
    )
    client = MagicMock()
    if error is not None:
        client.fetch_ohlcv.side_effect = error
    else:
        client.fetch_ohlcv.side_effect = list(pages or [])
    symbol_repo = MagicMock()
    symbol_repo.get_by_id.return_value = SimpleNamespace(symbol="BTC/USDT", exchange_id=1) if symbol else None
    timeframe_repo = MagicMock()
    timeframe_repo.get_by_id.return_value = SimpleNamespace(code="1h", seconds=3600) if timeframe else None
    exchange_repo = MagicMock()
    exchange_repo.get_by_id.return_value = SimpleNamespace(name=exchange) if exchange else None
    factory = MagicMock(return_value=client)
    svc = FetchCandleHistoryService(
        symbol_repo=symbol_repo,
        timeframe_repo=timeframe_repo,
        exchange_repo=exchange_repo,
        client_factory=factory,
    )
    return svc, client, factory


class TestFetchCandleHistoryService:

    def test_first_page_starts_bars_timeframes_ago(self, monkeypatch):
        now = 10 * STEP + STEP // 2
        svc, client, factory = _make(monkeypatch, pages=[_rows(6, 5)], now_ms=now)

        svc.fetch(symbol_id=1, timeframe_id=1, bars=4)

        factory.assert_called_once_with("binance")
        client.fetch_ohlcv.assert_called_once_with(
            "BTC/USDT", timeframe="1h", since=now - 4 * STEP, limit=1000
        )

    def test_returns_only_the_latest_bars_closed_candles(self, monkeypatch):
        # Llegan 0..10; la 10 está en formación → cerradas 0..9 → últimas 4: 6..9
        svc, _, _ = _make(monkeypatch, pages=[_rows(0, 11)])

        candles = svc.fetch(1, 1, bars=4).data

        assert [int(c.ts.timestamp() * 1000) // STEP for c in candles] == [6, 7, 8, 9]
        assert all(c.ts.tzinfo is not None for c in candles)

    def test_next_page_continues_after_the_last_candle(self, monkeypatch):
        svc, client, _ = _make(monkeypatch, pages=[_rows(0, 4), _rows(4, 7)])

        candles = svc.fetch(1, 1, bars=10).data

        assert client.fetch_ohlcv.call_args_list[1].kwargs["since"] == 4 * STEP
        assert len(candles) == 10

    def test_overlapping_pages_do_not_duplicate_candles(self, monkeypatch):
        svc, _, _ = _make(monkeypatch, pages=[_rows(0, 6), _rows(3, 8)])

        candles = svc.fetch(1, 1, bars=10).data

        stamps = [c.ts for c in candles]
        assert len(stamps) == len(set(stamps)) == 10

    def test_empty_page_stops_and_returns_what_it_has(self, monkeypatch):
        svc, client, _ = _make(monkeypatch, pages=[_rows(0, 3), []])

        result = svc.fetch(1, 1, bars=10)

        assert result.success is True
        assert len(result.data) == 3
        assert client.fetch_ohlcv.call_count == 2

    def test_stops_after_max_pages_if_exchange_ignores_since(self, monkeypatch):
        # Un exchange que devuelve siempre la misma vela vieja no deja el bucle colgado
        stuck = [[0, 100, 101, 99, 100, 5]]
        svc, client, _ = _make(monkeypatch, pages=[stuck] * 50)

        svc.fetch(1, 1, bars=10)

        assert client.fetch_ohlcv.call_count == history_module._MAX_PAGES

    def test_drops_invalid_rows_and_converts_to_decimal(self, monkeypatch):
        bad = {2: [2 * STEP, 100, 90, 99, 100, 5]}           # high < low
        none_volume = {3: [3 * STEP, 100, 101, 99, 100.5, None]}
        svc, _, _ = _make(monkeypatch, pages=[_rows(0, 11, {**bad, **none_volume})])

        candles = svc.fetch(1, 1, bars=10).data

        hours = [int(c.ts.timestamp() * 1000) // STEP for c in candles]
        assert 2 not in hours
        third = next(c for c in candles if int(c.ts.timestamp() * 1000) // STEP == 3)
        assert (third.close, third.volume) == (Decimal("100.5"), Decimal("0"))

    def test_row_with_null_price_is_dropped_instead_of_raising(self, monkeypatch):
        svc, _, _ = _make(monkeypatch, pages=[_rows(0, 11, {4: [4 * STEP, None, 101, 99, 100, 5]})])

        result = svc.fetch(1, 1, bars=10)

        assert result.success is True
        assert len(result.data) == 9

    @pytest.mark.parametrize("kwargs, code, status", [
        ({"symbol": False}, "SYMBOL_NOT_FOUND", 404),
        ({"timeframe": False}, "TIMEFRAME_NOT_FOUND", 404),
        ({"exchange": None}, "EXCHANGE_NOT_SUPPORTED_CCXT", 422),
        ({"exchange": "TradingView"}, "EXCHANGE_NOT_SUPPORTED_CCXT", 422),
        ({"error": ccxt.BadSymbol("x")}, "CCXT_SYMBOL_NOT_FOUND", 422),
        ({"error": ccxt.NetworkError("x")}, "CCXT_NETWORK_ERROR", 503),
        ({"error": ValueError("x")}, "CCXT_FETCH_ERROR", 502),
    ])
    def test_errors(self, monkeypatch, kwargs, code, status):
        svc, _, _ = _make(monkeypatch, **kwargs)

        result = svc.fetch(1, 1, bars=10)

        assert result.success is False
        assert (result.error.code, result.error.http_status) == (code, status)
