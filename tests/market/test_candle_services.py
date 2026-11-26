# -*- coding: utf-8 -*-

# ======================================================================
# tests/market/test_candle_services.py
#
# Velas de M2: ingesta manual (IngestCandlesService), lectura
# (ListCandlesService) y descarga con ccxt (FetchCandlesService).
# Nunca se llama a un exchange real: el cliente ccxt es un MagicMock
# inyectado por `client_cache` o sustituido con monkeypatch.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import ccxt
import pytest

from app.modules.market.services.candles import (
    FetchCandlesService,
    IngestCandlesService,
    ListCandlesService,
)
from app.modules.market.services.candles import fetch_candles_service as fetch_module

D = Decimal
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T0_MS = int(T0.timestamp() * 1000)
HOUR_MS = 3_600_000


def _repos(symbol=True, timeframe=True):
    candle_repo = MagicMock()
    candle_repo.bulk_upsert.side_effect = lambda candles: len(candles)
    symbol_repo = MagicMock()
    symbol_repo.get_by_id.return_value = (
        SimpleNamespace(id=1, symbol="BTC/USDT", exchange_id=1) if symbol else None
    )
    timeframe_repo = MagicMock()
    timeframe_repo.get_by_id.return_value = (
        SimpleNamespace(id=2, code="1h", seconds=3600) if timeframe else None
    )
    return candle_repo, symbol_repo, timeframe_repo


def _assert_failed(result, code, http_status, candle_repo):
    assert result.success is False
    assert result.error.code == code
    assert result.error.http_status == http_status
    candle_repo.bulk_upsert.assert_not_called()
    candle_repo.commit.assert_not_called()


# ======================================================================
# IngestCandlesService
# ======================================================================

def _row(ts=T0, o="100", h="110", low="90", c="105", v="12.5"):
    return {"ts": ts, "open": o, "high": h, "low": low, "close": c, "volume": v}


class TestIngestCandlesService:

    def _make(self, **kw):
        candle_repo, symbol_repo, timeframe_repo = _repos(**kw)
        return IngestCandlesService(candle_repo, symbol_repo, timeframe_repo), candle_repo

    def test_upserts_valid_rows_as_decimals_and_commits(self):
        svc, candle_repo = self._make()

        result = svc.ingest(symbol_id=1, timeframe_id=2, rows=[_row(), _row(c="107.25")])

        assert result.success is True
        assert (result.data.rows_received, result.data.rows_affected) == (2, 2)
        candles = candle_repo.bulk_upsert.call_args.args[0]
        assert [c.close for c in candles] == [D("105"), D("107.25")]
        assert all(isinstance(c.high, Decimal) for c in candles)
        assert {(c.symbol_id, c.timeframe_id) for c in candles} == {(1, 2)}
        candle_repo.commit.assert_called_once()

    def test_volume_defaults_to_zero(self):
        svc, candle_repo = self._make()
        row = _row()
        del row["volume"]

        svc.ingest(symbol_id=1, timeframe_id=2, rows=[row])

        assert candle_repo.bulk_upsert.call_args.args[0][0].volume == D("0")

    def test_unknown_symbol_is_404(self):
        svc, candle_repo = self._make(symbol=False)

        _assert_failed(svc.ingest(1, 2, [_row()]), "SYMBOL_NOT_FOUND", 404, candle_repo)

    def test_unknown_timeframe_is_404(self):
        svc, candle_repo = self._make(timeframe=False)

        _assert_failed(svc.ingest(1, 2, [_row()]), "TIMEFRAME_NOT_FOUND", 404, candle_repo)

    def test_empty_payload_is_422(self):
        svc, candle_repo = self._make()

        _assert_failed(svc.ingest(1, 2, []), "CANDLES_EMPTY_PAYLOAD", 422, candle_repo)

    def test_row_with_missing_field_reports_its_index(self):
        svc, candle_repo = self._make()
        broken = _row()
        del broken["close"]

        result = svc.ingest(1, 2, [_row(), broken])

        _assert_failed(result, "CANDLES_INVALID_ROW", 422, candle_repo)
        assert result.error.meta == {"row_index": 1}

    def test_row_with_non_numeric_price_is_invalid_row(self):
        svc, candle_repo = self._make()

        result = svc.ingest(1, 2, [_row(o="abc")])

        _assert_failed(result, "CANDLES_INVALID_ROW", 422, candle_repo)
        assert result.error.meta == {"row_index": 0}

    def test_high_below_low_rejects_the_whole_batch(self):
        svc, candle_repo = self._make()

        result = svc.ingest(1, 2, [_row(), _row(), _row(h="80", low="90")])

        _assert_failed(result, "CANDLES_INVALID_OHLCV", 422, candle_repo)
        assert result.error.meta == {"row_index": 2}

    def test_negative_price_is_invalid_ohlcv(self):
        svc, candle_repo = self._make()

        _assert_failed(svc.ingest(1, 2, [_row(c="-1")]), "CANDLES_INVALID_OHLCV", 422, candle_repo)

    def test_nan_price_is_invalid_ohlcv_instead_of_raising(self):
        svc, candle_repo = self._make()

        _assert_failed(svc.ingest(1, 2, [_row(c="NaN")]), "CANDLES_INVALID_OHLCV", 422, candle_repo)


# ======================================================================
# ListCandlesService
# ======================================================================

class TestListCandlesService:

    def _make(self, **kw):
        candle_repo, symbol_repo, timeframe_repo = _repos(**kw)
        candle_repo.list_candles.return_value = []
        return ListCandlesService(candle_repo, symbol_repo, timeframe_repo), candle_repo

    @pytest.mark.parametrize("requested, applied", [(5000, 1000), (1000, 1000), (50, 50), (0, 1), (-3, 1)])
    def test_limit_is_clamped_between_1_and_1000(self, requested, applied):
        svc, candle_repo = self._make()

        svc.list(symbol_id=1, timeframe_id=2, limit=requested)

        assert candle_repo.list_candles.call_args.kwargs["limit"] == applied

    def test_passes_date_range(self):
        svc, candle_repo = self._make()
        to_ts = datetime(2026, 2, 1, tzinfo=timezone.utc)

        svc.list(symbol_id=1, timeframe_id=2, from_ts=T0, to_ts=to_ts)

        kwargs = candle_repo.list_candles.call_args.kwargs
        assert (kwargs["from_ts"], kwargs["to_ts"]) == (T0, to_ts)

    def test_unknown_symbol_or_timeframe_is_404(self):
        svc, _ = self._make(symbol=False)
        assert svc.list(1, 2).error.code == "SYMBOL_NOT_FOUND"
        svc, _ = self._make(timeframe=False)
        assert svc.list(1, 2).error.code == "TIMEFRAME_NOT_FOUND"


# ======================================================================
# FetchCandlesService (ccxt mockeado)
# ======================================================================

def _ohlcv(i, o=100, h=110, low=90, c=105, v=3):
    return [T0_MS + i * HOUR_MS, o, h, low, c, v]


class TestFetchCandlesService:

    def _make(self, exchange_name: str | None = "Binance", **kw):
        candle_repo, symbol_repo, timeframe_repo = _repos(**kw)
        exchange_repo = MagicMock()
        exchange_repo.get_by_id.return_value = (
            SimpleNamespace(id=1, name=exchange_name) if exchange_name else None
        )
        svc = FetchCandlesService(candle_repo, symbol_repo, timeframe_repo, exchange_repo)
        return svc, candle_repo

    @staticmethod
    def _client(rows=None, error=None) -> MagicMock:
        client = MagicMock()
        if error is not None:
            client.fetch_ohlcv.side_effect = error
        else:
            client.fetch_ohlcv.return_value = rows
        return client

    def test_converts_rows_saves_them_and_commits(self):
        svc, candle_repo = self._make()
        client = self._client([_ohlcv(0), _ohlcv(1, c=106.5, v=None)])

        result = svc.fetch(symbol_id=1, timeframe_id=2, limit=2, client_cache={"binance": client})

        assert result.success is True
        assert result.data == {
            "exchange": "Binance", "symbol": "BTC/USDT", "timeframe": "1h",
            "rows_fetched": 2, "rows_affected": 2,
        }
        client.fetch_ohlcv.assert_called_once_with("BTC/USDT", timeframe="1h", limit=2)
        candles = candle_repo.bulk_upsert.call_args.args[0]
        assert candles[0].ts == T0
        assert candles[1].close == D("106.5")
        assert candles[1].volume == D("0")       # volumen nulo → 0
        candle_repo.commit.assert_called_once()

    def test_drops_invalid_ohlcv_rows_and_keeps_the_rest(self):
        svc, candle_repo = self._make()
        client = self._client([_ohlcv(0), _ohlcv(1, h=80, low=90), _ohlcv(2, c=-1)])

        result = svc.fetch(1, 2, client_cache={"binance": client})

        assert result.data["rows_fetched"] == 1
        assert len(candle_repo.bulk_upsert.call_args.args[0]) == 1

    def test_row_with_null_price_is_dropped_instead_of_raising(self):
        # Un exchange puede devolver un precio nulo en una vela sin datos:
        # se descarta esa fila, no se cae toda la descarga.
        svc, candle_repo = self._make()
        client = self._client([_ohlcv(0), _ohlcv(1, o=None), _ohlcv(2, c=float("nan"))])

        result = svc.fetch(1, 2, client_cache={"binance": client})

        assert result.success is True
        assert result.data["rows_fetched"] == 1

    def test_all_rows_invalid_is_empty_payload_without_commit(self):
        svc, candle_repo = self._make()
        client = self._client([_ohlcv(0, h=80, low=90)])

        _assert_failed(svc.fetch(1, 2, client_cache={"binance": client}), "CANDLES_EMPTY_PAYLOAD", 422, candle_repo)

    def test_exchange_returns_nothing(self):
        svc, candle_repo = self._make()

        _assert_failed(svc.fetch(1, 2, client_cache={"binance": self._client([])}), "CANDLES_EMPTY_PAYLOAD", 422, candle_repo)

    @pytest.mark.parametrize("error, code, status", [
        (ccxt.BadSymbol("no existe"), "CCXT_SYMBOL_NOT_FOUND", 422),
        (ccxt.NetworkError("timeout"), "CCXT_NETWORK_ERROR", 503),
        (ccxt.RequestTimeout("timeout"), "CCXT_NETWORK_ERROR", 503),
        (RuntimeError("raro"), "CCXT_FETCH_ERROR", 502),
    ])
    def test_ccxt_errors_map_to_codes(self, error, code, status):
        svc, candle_repo = self._make()

        result = svc.fetch(1, 2, client_cache={"binance": self._client(error=error)})

        _assert_failed(result, code, status, candle_repo)

    def test_unknown_symbol_timeframe_or_exchange(self):
        svc, repo = self._make(symbol=False)
        _assert_failed(svc.fetch(1, 2), "SYMBOL_NOT_FOUND", 404, repo)
        svc, repo = self._make(timeframe=False)
        _assert_failed(svc.fetch(1, 2), "TIMEFRAME_NOT_FOUND", 404, repo)
        svc, repo = self._make(exchange_name=None)
        _assert_failed(svc.fetch(1, 2), "EXCHANGE_NOT_FOUND", 404, repo)

    def test_exchange_without_ccxt_is_422_with_its_name(self):
        svc, candle_repo = self._make(exchange_name="TradingView")

        result = svc.fetch(1, 2)

        _assert_failed(result, "EXCHANGE_NOT_SUPPORTED_CCXT", 422, candle_repo)
        assert result.error.meta == {"exchange": "TradingView"}

    def test_client_is_created_once_and_reused_from_cache(self, monkeypatch):
        client = self._client([_ohlcv(0)])
        factory = MagicMock(return_value=client)
        monkeypatch.setattr(fetch_module.ccxt, "binance", factory)
        svc, _ = self._make()
        cache: dict = {}

        svc.fetch(1, 2, client_cache=cache)
        svc.fetch(1, 2, client_cache=cache)

        factory.assert_called_once_with({"enableRateLimit": True})
        assert cache == {"binance": client}
        assert client.fetch_ohlcv.call_count == 2
