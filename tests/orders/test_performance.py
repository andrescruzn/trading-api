# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_performance.py
#
# Métricas de rendimiento (domain/performance.py) y los servicios que las
# exponen: por agente y track record por estrategia.
# ======================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from app.modules.orders.domain.performance import TradeFill, compute_performance
from app.modules.orders.services.performance import get_bot_performance_service as bot_module
from app.modules.orders.services.performance import (
    GetBotPerformanceService,
    ListStrategyTrackRecordService,
)

D = Decimal
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc)


def _fill(side, qty, price, minutes, fee="0"):
    return TradeFill(side=side, qty=D(qty), price=D(price), fee=D(fee), ts=T0 + timedelta(minutes=minutes))


def _round_trip(start, buy, sell, qty="1"):
    return [_fill("buy", qty, buy, start), _fill("sell", qty, sell, start + 1)]


class TestComputePerformance:

    def test_no_fills_has_no_metrics(self):
        perf = compute_performance([])

        assert perf.trades == 0
        assert perf.win_rate is None
        assert perf.profit_factor is None
        assert perf.realized_pnl == D("0")

    def test_counts_win_and_loss_trades(self):
        # +20, −10, +30 → 2 ganadoras de 3
        fills = (
            _round_trip(0, "100", "120")
            + _round_trip(10, "100", "90")
            + _round_trip(20, "100", "130")
        )

        perf = compute_performance(fills)

        assert perf.trades == 3
        assert (perf.wins, perf.losses) == (2, 1)
        assert perf.win_rate == D(2) / D(3)
        assert perf.realized_pnl == D("40")
        assert perf.profit_factor == D("5")       # 50 / 10
        assert perf.avg_win == D("25")
        assert perf.avg_loss == D("10")
        assert perf.payoff_ratio == D("2.5")

    def test_max_drawdown_from_peak_of_cumulative_pnl(self):
        # Acumulado: +30 → +10 → −10 → +20: caída máxima 40 (de 30 a −10)
        fills = (
            _round_trip(0, "100", "130")
            + _round_trip(10, "100", "80")
            + _round_trip(20, "100", "80")
            + _round_trip(30, "100", "130")
        )

        perf = compute_performance(fills)

        assert perf.max_drawdown == D("40")
        assert [v for _, v in perf.equity_curve] == [D("30"), D("10"), D("-10"), D("20")]

    def test_scaling_in_counts_as_one_trade_with_weighted_average(self):
        # Compra 1 @ 100 y 1 @ 200 (prom. 150), vende 2 @ 180 → +60 en una operación
        fills = [
            _fill("buy", "1", "100", 0),
            _fill("buy", "1", "200", 1),
            _fill("sell", "2", "180", 2),
        ]

        perf = compute_performance(fills)

        assert perf.trades == 1
        assert perf.closed_trades[0].pnl == D("60")
        assert perf.closed_trades[0].cost == D("300")
        assert perf.closed_trades[0].return_pct == D("0.2")

    def test_open_position_is_not_a_closed_trade(self):
        fills = [_fill("buy", "2", "100", 0), _fill("sell", "1", "110", 1)]

        perf = compute_performance(fills)

        assert perf.trades == 0
        assert perf.open_qty == D("1")
        assert perf.open_avg_price == D("100")
        assert perf.open_realized_pnl == D("10")

    def test_fills_are_sorted_by_time(self):
        fills = list(reversed(_round_trip(0, "100", "110")))

        perf = compute_performance(fills)

        assert perf.trades == 1
        assert perf.realized_pnl == D("10")

    def test_fees_are_summed_apart_from_pnl(self):
        fills = [_fill("buy", "1", "100", 0, fee="0.1"), _fill("sell", "1", "110", 1, fee="0.2")]

        perf = compute_performance(fills)

        assert perf.total_fees == D("0.3")
        assert perf.realized_pnl == D("10")

    def test_sell_without_position_is_ignored(self):
        perf = compute_performance([_fill("sell", "1", "100", 0)])

        assert perf.trades == 0
        assert perf.open_qty == D("0")


class TestGetBotPerformanceService:

    def _make(self, monkeypatch, bot, fills, close=None):
        monkeypatch.setattr(bot_module, "find_accessible_bot", lambda *args: bot)
        fill_repo = MagicMock()
        fill_repo.list_trade_fills_by_bots.return_value = {bot.id: fills} if bot else {}
        candle_repo = MagicMock()
        candle_repo.list_candles.return_value = [MagicMock(close=close)] if close else []
        svc = GetBotPerformanceService(
            fill_repo=fill_repo,
            bot_repo=MagicMock(),
            account_repo=MagicMock(),
            candle_repo=candle_repo,
            funding_repo=MagicMock(),
        )
        return svc, candle_repo

    @staticmethod
    def _bot():
        bot = MagicMock()
        bot.id, bot.symbol_id, bot.timeframe_id = 5, 1, 2
        return bot

    def test_foreign_bot_is_not_found(self, monkeypatch):
        svc, _ = self._make(monkeypatch, None, [])

        result = svc.get(bot_id=5, owner_id=9)

        assert result.error.code == "BOT_NOT_FOUND"
        assert result.error.http_status == 404

    def test_unrealized_pnl_uses_last_close(self, monkeypatch):
        svc, _ = self._make(monkeypatch, self._bot(), [_fill("buy", "2", "100", 0)], close="110")

        result = svc.get(bot_id=5)

        assert result.data.last_price == D("110")
        assert result.data.unrealized_pnl == D("20")

    def test_flat_bot_does_not_read_candles(self, monkeypatch):
        svc, candle_repo = self._make(monkeypatch, self._bot(), _round_trip(0, "100", "110"))

        result = svc.get(bot_id=5)

        assert result.data.performance.trades == 1
        assert result.data.unrealized_pnl is None
        candle_repo.list_candles.assert_not_called()


class TestListStrategyTrackRecordService:

    @staticmethod
    def _bot(bot_id, strategy_id, mode="paper"):
        bot = MagicMock()
        bot.id, bot.strategy_id, bot.mode = bot_id, strategy_id, mode
        return bot

    def _make(self, bots, fills_by_bot):
        bot_repo = MagicMock()
        bot_repo.list_all.return_value = bots
        fill_repo = MagicMock()
        fill_repo.list_trade_fills_by_bots.side_effect = lambda ids: {
            i: fills_by_bot.get(i, []) for i in ids
        }
        strategy = MagicMock()
        strategy.id, strategy.name, strategy.version = 1, "Tendencia", "1.0"
        strategy_repo = MagicMock()
        strategy_repo.list_all.return_value = [strategy]
        return ListStrategyTrackRecordService(
            fill_repo=fill_repo, bot_repo=bot_repo, strategy_repo=strategy_repo
        )

    def test_aggregates_returns_of_all_agents_of_a_strategy(self):
        # Dos agentes con tamaños distintos: se suman RETORNOS, no montos
        svc = self._make(
            [self._bot(1, 1), self._bot(2, 1)],
            {
                1: _round_trip(0, "100", "110"),                # +10 %
                2: _round_trip(10, "1000", "950", qty="5"),     # −5 %
            },
        )

        records = svc.list().data

        assert len(records) == 1
        record = records[0]
        assert record.strategy_name == "Tendencia v1.0"
        assert (record.agents, record.trades, record.wins) == (2, 2, 1)
        assert record.total_return_pct == D("0.05")
        assert record.profit_factor == D("2")          # 0.10 / 0.05
        assert record.max_drawdown_pct == D("0.05")

    def test_paper_and_live_are_separate_records(self):
        svc = self._make(
            [self._bot(1, 1, "paper"), self._bot(2, 1, "live")],
            {1: _round_trip(0, "100", "110"), 2: _round_trip(0, "100", "110")},
        )

        modes = sorted(r.mode for r in svc.list().data)

        assert modes == ["live", "paper"]

    def test_filter_by_mode(self):
        svc = self._make(
            [self._bot(1, 1, "paper"), self._bot(2, 1, "live")],
            {1: _round_trip(0, "100", "110"), 2: _round_trip(0, "100", "110")},
        )

        records = svc.list(mode="live").data

        assert [r.mode for r in records] == ["live"]

    def test_strategy_without_closed_trades_still_listed(self):
        svc = self._make([self._bot(1, 1)], {1: [_fill("buy", "1", "100", 0)]})

        record = svc.list().data[0]

        assert record.trades == 0
        assert record.win_rate is None
