# -*- coding: utf-8 -*-

# ======================================================================
# tests/market/test_trend_explorer.py
#
# Explorador de tendencia de M2:
# - compute_trend_metrics (función pura, pandas-ta real) con series
#   sintéticas de números conocidos: ADX, eficiencia de Kaufman,
#   rendimientos, ATR %, dirección, fuerza y score.
# - ListTrendExplorerService: filtro por descarga automática y orden.
# - RefreshExplorerCandlesService: qué símbolos se descargan y cuántas
#   velas, con `force` y con fallos aislados.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.contracts import ServiceResult
from app.modules.market.domain.candle_entity import Candle
from app.modules.market.domain.symbol_entity import Symbol
from app.modules.market.services.explorer import (
    ListTrendExplorerService,
    RefreshExplorerCandlesService,
)
from app.modules.market.services.explorer import list_trend_explorer_service as list_module
from app.modules.market.services.explorer import refresh_explorer_candles_service as refresh_module
from app.modules.market.services.explorer import trend_metrics
from app.modules.market.services.explorer.trend_metrics import TrendMetrics, compute_trend_metrics

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _daily(closes: list[float], spread: float = 0.5) -> list[Candle]:
    """Velas 1d con high/low a ±spread del cierre."""
    return [
        Candle(
            id=0, symbol_id=1, timeframe_id=1, ts=T0 + timedelta(days=i),
            open=Decimal(str(c)), high=Decimal(str(c + spread)), low=Decimal(str(c - spread)),
            close=Decimal(str(c)), volume=Decimal("1"),
        )
        for i, c in enumerate(closes)
    ]


def _walk(start: float, steps: list[float], n: int) -> list[float]:
    """Serie de n cierres que repite el patrón de pasos."""
    closes = [start]
    for i in range(n - 1):
        closes.append(closes[-1] + steps[i % len(steps)])
    return closes


# ======================================================================
# compute_trend_metrics
# ======================================================================

class TestComputeTrendMetrics:

    def test_needs_at_least_60_daily_candles(self):
        assert compute_trend_metrics(_daily([100 + i for i in range(59)])) is None
        assert compute_trend_metrics(_daily([100 + i for i in range(60)])) is not None

    def test_straight_uptrend_has_max_strength_and_positive_score(self):
        # +1 por día, rango fijo de 1: +DM = 1, −DM = 0 → ADX 100; línea recta → eficiencia 1
        m = compute_trend_metrics(_daily([100 + i for i in range(250)]))

        assert m.candles == 250
        assert m.last_close == 349.0
        assert m.last_ts == T0 + timedelta(days=249)
        assert m.adx_14 == pytest.approx(100.0)
        assert m.efficiency_30 == pytest.approx(1.0)
        assert m.ret_30d == pytest.approx(349 / 319 - 1)
        assert m.ret_90d == pytest.approx(349 / 259 - 1)
        # TR = |high − cierre anterior| = 1,5 → ATR 1,5 / 349
        assert m.atr_pct_14 == pytest.approx(1.5 / 349, rel=1e-4)
        assert (m.direction, m.strength, m.score) == ("up", 100.0, 100.0)

    def test_straight_downtrend_has_negative_score(self):
        m = compute_trend_metrics(_daily([400 - i for i in range(250)]))

        assert m.direction == "down"
        assert m.strength == 100.0
        assert m.score == -100.0
        assert m.ret_30d == pytest.approx(151 / 181 - 1)

    def test_strength_is_adx_over_50_times_efficiency(self):
        # Patrón +2, −1: en 30 cambios hay 15 de cada → neto 15, recorrido 45 → eficiencia 1/3
        m = compute_trend_metrics(_daily(_walk(100.0, [2, -1], 250)))

        assert m.efficiency_30 == pytest.approx(1 / 3)
        assert 25 < m.adx_14 < 50                     # tendencia, pero sin la fuerza máxima
        assert m.strength == round(m.adx_14 / 50 * (1 / 3) * 100, 2)
        assert m.strength == pytest.approx(22.28, abs=0.01)
        assert (m.direction, m.score) == ("up", m.strength)

    def test_adx_is_capped_at_50_for_full_strength(self):
        # ADX 100 cuenta como 1 (no 2): la fuerza no supera 100
        m = compute_trend_metrics(_daily([100 + 2 * i for i in range(250)]))

        assert m.adx_14 > 50
        assert m.strength == 100.0

    def test_pure_zigzag_is_sideways_with_zero_strength(self):
        m = compute_trend_metrics(_daily([100 + (i % 2) for i in range(250)]))

        assert m.efficiency_30 == 0.0
        assert m.ret_30d == 0.0
        assert (m.direction, m.strength, m.score) == ("sideways", 0.0, 0.0)

    def test_low_adx_forces_sideways_even_with_aligned_emas(self, monkeypatch):
        # Sube 0,1 cada dos días con ruido de ±3: EMAs alineadas al alza pero ADX < 20
        closes = _walk(100.0, [3, -2.9], 250)
        m = compute_trend_metrics(_daily(closes))

        assert m.adx_14 < 20
        assert m.strength > 0
        assert (m.direction, m.score) == ("sideways", 0.0)

        monkeypatch.setattr(trend_metrics, "_ADX_TREND_MIN", 0.0)
        assert compute_trend_metrics(_daily(closes)).direction == "up"

    def test_without_200_candles_direction_uses_only_ema50(self):
        m = compute_trend_metrics(_daily([100 + i for i in range(100)]))

        assert m.direction == "up"
        assert m.ret_90d == pytest.approx(199 / 109 - 1)

    def test_ret_90d_is_none_with_90_candles_or_less(self):
        m = compute_trend_metrics(_daily([100 + i for i in range(80)]))

        assert m.ret_90d is None
        assert m.ret_30d == pytest.approx(179 / 149 - 1)

    def test_order_of_input_candles_does_not_matter(self):
        candles = _daily([100 + i for i in range(120)])

        assert compute_trend_metrics(list(reversed(candles))) == compute_trend_metrics(candles)


class TestTrendHelpers:

    @pytest.mark.parametrize("close, ema50, ema200, expected", [
        (110.0, 100.0, 90.0, "up"),
        (80.0, 90.0, 100.0, "down"),
        (110.0, 100.0, None, "up"),
        (90.0, 100.0, None, "down"),
        (110.0, 100.0, 120.0, "sideways"),   # sobre la EMA50 pero EMA50 < EMA200
        (90.0, 100.0, 80.0, "sideways"),
        (100.0, None, None, "sideways"),
    ])
    def test_direction(self, close, ema50, ema200, expected):
        assert trend_metrics._direction(close, ema50, ema200) == expected

    def test_efficiency_ratio_with_concrete_numbers(self):
        import pandas as pd

        # 4 cambios: +2, −1, +2, −1 → neto 2, recorrido 6
        assert trend_metrics._efficiency_ratio(pd.Series([10, 12, 11, 13, 12]), 4) == pytest.approx(2 / 6)
        assert trend_metrics._efficiency_ratio(pd.Series([10, 10, 10, 10, 10]), 4) is None   # sin recorrido
        assert trend_metrics._efficiency_ratio(pd.Series([10, 11, 12]), 4) is None          # sin datos

    def test_return_with_concrete_numbers(self):
        import pandas as pd

        assert trend_metrics._return(pd.Series([100.0, 105.0, 110.0]), 2) == pytest.approx(0.10)
        assert trend_metrics._return(pd.Series([100.0, 110.0]), 2) is None
        assert trend_metrics._return(pd.Series([0.0, 1.0, 2.0]), 2) is None


# ======================================================================
# ListTrendExplorerService
# ======================================================================

def _metrics(score: float, strength: float) -> TrendMetrics:
    direction = "up" if score > 0 else "down" if score < 0 else "sideways"
    return TrendMetrics(
        candles=250, last_close=1.0, last_ts=T0, ret_30d=0.0, ret_90d=0.0, adx_14=30.0,
        efficiency_30=0.5, atr_pct_14=0.01, direction=direction, strength=strength, score=score,
    )


def _symbol(id_: int, symbol: str, exchange_name: str = "Binance") -> Symbol:
    return Symbol(id=id_, exchange_id=1, symbol=symbol, asset_class="crypto", exchange_name=exchange_name)


class TestListTrendExplorerService:

    def _make(self, symbols, timeframe=SimpleNamespace(id=12, code="1d", seconds=86400)):
        symbol_repo = MagicMock()
        symbol_repo.list_all.return_value = symbols
        timeframe_repo = MagicMock()
        timeframe_repo.get_by_code.return_value = timeframe
        candle_repo = MagicMock()
        # Cada símbolo devuelve su id como "velas" para poder mapear métricas
        candle_repo.list_candles.side_effect = lambda symbol_id, timeframe_id, limit: symbol_id
        svc = ListTrendExplorerService(symbol_repo, timeframe_repo, candle_repo)
        return svc, symbol_repo, candle_repo

    def test_orders_by_score_with_no_data_last(self, monkeypatch):
        symbols = [
            _symbol(1, "DOWN/USDT"), _symbol(2, "NODATA/USDT"), _symbol(3, "FLAT/USDT"),
            _symbol(4, "WEAKUP/USDT"), _symbol(5, "STRONG/USDT"), _symbol(6, "TIE/USDT"),
        ]
        by_id = {
            1: _metrics(-60, 60), 2: None, 3: _metrics(0, 5),
            4: _metrics(20, 20), 5: _metrics(80, 80), 6: _metrics(0, 15),
        }
        monkeypatch.setattr(list_module, "compute_trend_metrics", lambda candles: by_id[candles])
        svc, _, _ = self._make(symbols)

        rows = svc.list().data

        # A igual score (0) va primero la de más fuerza
        assert [r.symbol.symbol for r in rows] == [
            "STRONG/USDT", "WEAKUP/USDT", "TIE/USDT", "FLAT/USDT", "DOWN/USDT", "NODATA/USDT",
        ]

    def test_skips_symbols_without_auto_fetch_and_flags_perpetuals(self, monkeypatch):
        monkeypatch.setattr(list_module, "compute_trend_metrics", lambda candles: None)
        symbols = [_symbol(1, "XAU/USDT:USDT"), _symbol(2, "BTC/USDT"), _symbol(3, "SPX", "TradingView")]
        svc, _, candle_repo = self._make(symbols)

        rows = svc.list().data

        assert [(r.symbol.symbol, r.is_perpetual) for r in rows] == [("XAU/USDT:USDT", True), ("BTC/USDT", False)]
        assert candle_repo.list_candles.call_count == 2

    def test_reads_250_daily_candles_of_active_symbols(self, monkeypatch):
        monkeypatch.setattr(list_module, "compute_trend_metrics", lambda candles: None)
        svc, symbol_repo, candle_repo = self._make([_symbol(7, "ETH/USDT")])

        svc.list(asset_class="crypto")

        symbol_repo.list_all.assert_called_once_with(asset_class="crypto", is_active=True)
        candle_repo.list_candles.assert_called_once_with(symbol_id=7, timeframe_id=12, limit=250)

    def test_missing_1d_timeframe_is_404(self):
        svc, _, _ = self._make([], timeframe=None)

        result = svc.list()

        assert (result.error.code, result.error.http_status) == ("EXPLORER_TIMEFRAME_MISSING", 404)


# ======================================================================
# RefreshExplorerCandlesService
# ======================================================================

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)


class TestRefreshExplorerCandlesService:

    def _make(self, monkeypatch, symbols, latest_by_id, fetch_results=None,
              timeframe=SimpleNamespace(id=12, code="1d", seconds=86400)):
        monkeypatch.setattr(refresh_module, "utc_now", lambda: NOW)
        symbol_repo = MagicMock()
        symbol_repo.list_all.return_value = symbols
        timeframe_repo = MagicMock()
        timeframe_repo.get_by_code.return_value = timeframe
        candle_repo = MagicMock()
        candle_repo.get_latest_ts.side_effect = lambda symbol_id, tf_id: latest_by_id.get(symbol_id)
        fetch = MagicMock()
        results = fetch_results or {}
        fetch.fetch.side_effect = lambda symbol_id, **kw: results.get(symbol_id, ServiceResult.ok({}))
        svc = RefreshExplorerCandlesService(symbol_repo, timeframe_repo, candle_repo, fetch)
        return svc, fetch

    @staticmethod
    def _limits(fetch: MagicMock) -> dict[int, int]:
        return {c.kwargs["symbol_id"]: c.kwargs["limit"] for c in fetch.fetch.call_args_list}

    def test_limit_depends_on_how_many_days_are_missing(self, monkeypatch):
        symbols = [_symbol(1, "NEW/USDT"), _symbol(2, "LATE/USDT"), _symbol(3, "OLD/USDT"), _symbol(4, "TODAY/USDT")]
        latest = {
            2: NOW - timedelta(days=3, hours=1),   # 3 días atrás → 3 + 2 de margen
            3: NOW - timedelta(days=400),          # tope 250
            4: NOW - timedelta(hours=12),          # al día → se omite
        }
        svc, fetch = self._make(monkeypatch, symbols, latest)

        data = svc.refresh().data

        assert self._limits(fetch) == {1: 250, 2: 5, 3: 250}
        assert data == {"updated": ["NEW/USDT", "LATE/USDT", "OLD/USDT"], "skipped": ["TODAY/USDT"], "failed": []}

    def test_force_downloads_up_to_date_symbols_too(self, monkeypatch):
        svc, fetch = self._make(monkeypatch, [_symbol(4, "TODAY/USDT")], {4: NOW - timedelta(hours=12)})

        data = svc.refresh(force=True).data

        assert self._limits(fetch) == {4: 2}
        assert data["updated"] == ["TODAY/USDT"]

    def test_one_failure_does_not_stop_the_rest(self, monkeypatch):
        symbols = [_symbol(1, "BAD/USDT"), _symbol(2, "GOOD/USDT")]
        failures = {1: ServiceResult.fail(code="CCXT_SYMBOL_NOT_FOUND", http_status=422)}
        svc, _ = self._make(monkeypatch, symbols, {}, fetch_results=failures)

        data = svc.refresh().data

        assert data["failed"] == [{"symbol": "BAD/USDT", "code": "CCXT_SYMBOL_NOT_FOUND"}]
        assert data["updated"] == ["GOOD/USDT"]

    def test_skips_exchanges_without_auto_fetch_and_shares_one_client_cache(self, monkeypatch):
        symbols = [_symbol(1, "A/USDT"), _symbol(2, "B", "TradingView"), _symbol(3, "C/USDT")]
        svc, fetch = self._make(monkeypatch, symbols, {})

        svc.refresh()

        caches = [c.kwargs["client_cache"] for c in fetch.fetch.call_args_list]
        assert len(caches) == 2
        assert caches[0] is caches[1]
        assert all(c.kwargs["timeframe_id"] == 12 for c in fetch.fetch.call_args_list)

    def test_missing_1d_timeframe_is_404(self, monkeypatch):
        svc, fetch = self._make(monkeypatch, [], {}, timeframe=None)

        result = svc.refresh()

        assert (result.error.code, result.error.http_status) == ("EXPLORER_TIMEFRAME_MISSING", 404)
        fetch.fetch.assert_not_called()
