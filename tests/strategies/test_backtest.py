# -*- coding: utf-8 -*-

# ======================================================================
# tests/strategies/test_backtest.py
#
# Motor de backtesting (domain/backtest.py), servicio que lo arma con
# historia e indicadores reales en memoria, e historial paginado del
# exchange (sin red: cliente falso).
# ======================================================================

import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.common.contracts import ServiceResult
from app.modules.market.domain.candle_entity import Candle
from app.modules.market.services.candles import FetchCandleHistoryService
from app.modules.market.services.candles import fetch_candle_history_service as history_module
from app.modules.strategies.domain.backtest import BacktestBar, BacktestConfig, run_backtest
from app.modules.strategies.services.backtests import RunBacktestService

D = Decimal
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
ALWAYS = [{"indicator": "rsi_14", "operator": "gt", "value": 0}]
NO_FEES = BacktestConfig(fee_pct=D("0"))


def _bar(i, o, h, low, c, atr="10", regime="trend_up", rsi=50):
    features = {"atr_14": float(atr), "regime": regime, "rsi_14": rsi} if atr is not None else None
    return BacktestBar(
        ts=T0 + timedelta(hours=i), open=D(o), high=D(h), low=D(low), close=D(c), features=features
    )


class TestRunBacktest:

    def test_enters_next_open_and_exits_at_take_profit(self):
        # Señal en la vela 0; entra en la apertura de la 1 (100) con ATR 10:
        # SL 85, TP 130. La vela 2 toca 130 → +30 por unidad.
        bars = [
            _bar(0, "100", "101", "99", "100"),
            _bar(1, "100", "110", "95", "105", atr=None),
            _bar(2, "105", "131", "104", "130", atr=None),
        ]

        result = run_backtest(bars, ALWAYS, None, NO_FEES)

        trade = result.trades[0]
        assert (trade.entry_price, trade.stop_loss, trade.take_profit) == (D("100"), D("85"), D("130"))
        assert trade.exit_reason == "take_profit"
        assert trade.exit_price == D("130")
        # Riesgo 1 % de 10.000 = 100; riesgo por unidad 15 → qty 6,666…
        assert trade.qty == D("100") / D("15")
        assert result.final_capital == D("10000") + trade.qty * D("30")

    def test_stop_loss_wins_when_both_levels_are_touched(self):
        bars = [
            _bar(0, "100", "101", "99", "100"),
            _bar(1, "100", "140", "80", "100", atr=None),
        ]

        trade = run_backtest(bars, ALWAYS, None, NO_FEES).trades[0]

        assert trade.exit_reason == "stop_loss"
        assert trade.exit_price == D("85")

    def test_gap_below_stop_exits_at_open(self):
        bars = [
            _bar(0, "100", "101", "99", "100"),
            _bar(1, "100", "101", "99", "100", atr=None),
            _bar(2, "70", "72", "65", "70", atr=None),   # abre bajo el SL (85)
        ]

        trade = run_backtest(bars, ALWAYS, None, NO_FEES).trades[0]

        assert trade.exit_price == D("70")

    def test_no_signal_when_regime_does_not_match(self):
        bars = [_bar(i, "100", "101", "99", "100", regime="sideways") for i in range(5)]

        result = run_backtest(bars, ALWAYS, "trend_up", NO_FEES)

        assert result.trades == []
        assert result.signals == 0

    def test_trend_down_strategy_never_opens_in_spot(self):
        bars = [_bar(i, "100", "101", "99", "100", regime="trend_down") for i in range(5)]

        assert run_backtest(bars, ALWAYS, "trend_down", NO_FEES).trades == []

    def test_rules_must_pass(self):
        rules = [{"indicator": "rsi_14", "operator": "lt", "value": 30}]
        bars = [_bar(i, "100", "101", "99", "100", rsi=50) for i in range(5)]

        assert run_backtest(bars, rules, None, NO_FEES).trades == []

    def test_open_position_is_closed_at_last_close(self):
        bars = [
            _bar(0, "100", "101", "99", "100"),
            _bar(1, "100", "102", "99", "101", atr=None),
            _bar(2, "101", "103", "100", "102", atr=None),
        ]

        trade = run_backtest(bars, ALWAYS, None, NO_FEES).trades[0]

        assert trade.exit_reason == "end"
        assert trade.exit_price == D("102")

    def test_signals_while_in_position_are_skipped(self):
        bars = [_bar(i, "100", "101", "99", "100") for i in range(4)]

        result = run_backtest(bars, ALWAYS, None, NO_FEES)

        assert len(result.trades) == 1
        assert result.skipped_in_position >= 1

    def test_fees_reduce_pnl(self):
        bars = [
            _bar(0, "100", "101", "99", "100"),
            _bar(1, "100", "131", "95", "130", atr=None),
        ]

        trade = run_backtest(bars, ALWAYS, None, BacktestConfig(fee_pct=D("0.001"))).trades[0]

        gross = (trade.exit_price - trade.entry_price) * trade.qty
        assert trade.fees == trade.qty * D("100") * D("0.001") + trade.qty * D("130") * D("0.001")
        assert trade.pnl == gross - trade.fees

    def test_position_never_costs_more_than_capital(self):
        # ATR minúsculo → por riesgo compraría muchísimo: se limita al capital
        bars = [
            _bar(0, "100", "101", "99", "100", atr="0.01"),
            _bar(1, "100", "101", "99", "100", atr=None),
        ]

        trade = run_backtest(bars, ALWAYS, None, NO_FEES).trades[0]

        assert trade.entry_price * trade.qty <= D("10000")

    def test_buy_and_hold_comparison(self):
        bars = [_bar(0, "100", "101", "99", "100", atr=None), _bar(1, "100", "121", "99", "120", atr=None)]

        assert run_backtest(bars, ALWAYS, None, NO_FEES).buy_and_hold_pct == D("0.2")


def _synthetic_candles(n, start=100.0):
    candles = []
    for i in range(n):
        close = start + 10 * math.sin(i / 8) + i * 0.05
        candles.append(
            Candle(
                id=0,
                symbol_id=1,
                timeframe_id=1,
                ts=T0 + timedelta(hours=i),
                open=D(str(round(close - 0.5, 4))),
                high=D(str(round(close + 2, 4))),
                low=D(str(round(close - 2, 4))),
                close=D(str(round(close, 4))),
                volume=D("1000"),
            )
        )
    return candles


class TestRunBacktestService:

    def _make(self, strategy, history):
        strategy_repo = MagicMock()
        strategy_repo.get_by_id.return_value = strategy
        fetch = MagicMock()
        fetch.fetch.return_value = history
        return RunBacktestService(strategy_repo=strategy_repo, fetch_history=fetch), fetch

    @staticmethod
    def _strategy(rules=ALWAYS, regime=None, risk="0.05"):
        return SimpleNamespace(
            name="Prueba", version="1.0", rules=rules, regime_required=regime,
            parameters={"risk_pct": risk},
        )

    def test_runs_on_real_indicators_and_caps_risk_at_one_percent(self):
        svc, fetch = self._make(self._strategy(), ServiceResult.ok(_synthetic_candles(900)))

        result = svc.run(strategy_id=1, symbol_id=1, timeframe_id=1, bars=500)

        assert result.success is True
        report = result.data
        assert report.config.risk_pct == D("0.01")       # 5 % pedido → tope 1 %
        assert report.result.bars == 500
        assert report.result.signals > 0                 # los indicadores se encontraron por fecha
        assert report.performance.trades == len(report.result.trades)
        fetch.fetch.assert_called_once()
        assert fetch.fetch.call_args.args[2] > 500       # pide velas de calentamiento

    def test_not_enough_history(self):
        svc, _ = self._make(self._strategy(), ServiceResult.ok(_synthetic_candles(100)))

        result = svc.run(strategy_id=1, symbol_id=1, timeframe_id=1, bars=500)

        assert result.error.code == "BACKTEST_NOT_ENOUGH_HISTORY"

    def test_strategy_without_rules(self):
        svc, fetch = self._make(self._strategy(rules=[]), ServiceResult.ok([]))

        result = svc.run(strategy_id=1, symbol_id=1, timeframe_id=1, bars=500)

        assert result.error.code == "BACKTEST_STRATEGY_WITHOUT_RULES"
        fetch.fetch.assert_not_called()

    def test_history_failure_is_returned(self):
        svc, _ = self._make(self._strategy(), ServiceResult.fail(code="CCXT_NETWORK_ERROR", http_status=503))

        assert svc.run(1, 1, 1, 500).error.code == "CCXT_NETWORK_ERROR"


class TestFetchCandleHistoryService:

    def _make(self, monkeypatch, pages, now_ms):
        monkeypatch.setattr(
            history_module, "utc_now",
            lambda: datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc),
        )
        client = MagicMock()
        client.fetch_ohlcv.side_effect = pages
        symbol_repo = MagicMock()
        symbol_repo.get_by_id.return_value = SimpleNamespace(symbol="BTC/USDT", exchange_id=1)
        timeframe_repo = MagicMock()
        timeframe_repo.get_by_id.return_value = SimpleNamespace(code="1h", seconds=3600)
        exchange_repo = MagicMock()
        exchange_repo.get_by_id.return_value = SimpleNamespace(name="Binance")
        svc = FetchCandleHistoryService(
            symbol_repo=symbol_repo,
            timeframe_repo=timeframe_repo,
            exchange_repo=exchange_repo,
            client_factory=lambda ccxt_id: client,
        )
        return svc, client

    @staticmethod
    def _rows(start_ms, n):
        step = 3_600_000
        return [[start_ms + i * step, 100, 101, 99, 100, 5] for i in range(n)]

    def test_pages_until_now_and_drops_forming_candle(self, monkeypatch):
        step = 3_600_000
        now = 10 * step + step // 2              # la vela 10 está en formación
        pages = [self._rows(0, 6), self._rows(6 * step, 5)]
        svc, client = self._make(monkeypatch, pages, now)

        candles = svc.fetch(symbol_id=1, timeframe_id=1, bars=10).data

        assert client.fetch_ohlcv.call_count == 2
        assert len(candles) == 10                # 0..9; la 10 no se incluye
        assert candles[0].ts < candles[-1].ts

    def test_unsupported_exchange(self, monkeypatch):
        svc, _ = self._make(monkeypatch, [], 0)
        svc._exchange_repo.get_by_id.return_value = SimpleNamespace(name="Desconocido")

        assert svc.fetch(1, 1, 10).error.code == "EXCHANGE_NOT_SUPPORTED_CCXT"
