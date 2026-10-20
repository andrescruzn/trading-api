# -*- coding: utf-8 -*-

# ======================================================================
# tests/alerts/test_rule_conditions.py
#
# Condiciones puras de las reglas periódicas: precio, P&L, drawdown y
# antispam (app/modules/alerts/domain/rule_conditions.py).
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

from app.modules.alerts.domain.rule_conditions import (
    BotPnlSnapshot,
    bot_pnl_snapshot,
    daily_pnl_pct,
    drawdown_condition_met,
    in_cooldown,
    pnl_condition_met,
    price_condition_met,
)
from app.modules.orders.domain.performance import TradeFill, compute_performance

T0 = datetime(2026, 10, 1, tzinfo=timezone.utc)


def _fill(side: str, qty: str, price: str, minutes: int) -> TradeFill:
    return TradeFill(side=side, qty=D(qty), price=D(price), fee=D("0"), ts=T0 + timedelta(minutes=minutes))


def _example_fills() -> list[TradeFill]:
    """+40 (costo 1.000), −20 (costo 800) y una posición abierta de 0,01 a 60.000 (costo 600)."""
    return [
        _fill("buy", "1", "1000", 0), _fill("sell", "1", "1040", 10),
        _fill("buy", "1", "800", 20), _fill("sell", "1", "780", 30),
        _fill("buy", "0.01", "60000", 40),
    ]


class TestPriceCondition:

    def test_below_operators(self):
        assert price_condition_met(D("79999"), "lt", D("80000")) is True
        assert price_condition_met(D("80000"), "lt", D("80000")) is False
        assert price_condition_met(D("80000"), "lte", D("80000")) is True
        assert price_condition_met(D("80001"), "lte", D("80000")) is False

    def test_above_operators(self):
        assert price_condition_met(D("62001"), "gt", D("62000")) is True
        assert price_condition_met(D("62000"), "gt", D("62000")) is False
        assert price_condition_met(D("62000"), "gte", D("62000")) is True
        assert price_condition_met(D("61999"), "gte", D("62000")) is False

    def test_unknown_operator_never_matches(self):
        assert price_condition_met(D("1"), "between", D("0")) is False


class TestBotPnlSnapshot:

    def test_example_from_module_header(self):
        snap = bot_pnl_snapshot(compute_performance(_example_fills()), last_price=D("57000"))

        assert snap.invested == D("1000")            # la mayor inversión de una operación
        assert snap.total_pnl == D("-10")            # 40 − 20 − 30 no realizado
        assert snap.pnl_pct == D("-1")
        assert snap.peak_pnl == D("40")
        assert snap.drawdown == D("50")
        assert snap.drawdown_pct == D("5")

    def test_without_price_the_open_position_counts_at_cost(self):
        snap = bot_pnl_snapshot(compute_performance(_example_fills()), last_price=None)

        assert snap.total_pnl == D("20")
        assert snap.drawdown == D("20")

    def test_partial_sale_of_open_trade_counts_as_pnl(self):
        fills = [_fill("buy", "2", "100", 0), _fill("sell", "1", "90", 5)]
        snap = bot_pnl_snapshot(compute_performance(fills), last_price=D("80"))

        # −10 vendido + (80 − 100) × 1 abierto = −30 sobre 100 de costo abierto
        assert snap.total_pnl == D("-30")
        assert snap.invested == D("100")
        assert snap.pnl_pct == D("-30")

    def test_without_trades_percentages_are_none(self):
        snap = bot_pnl_snapshot(compute_performance([]), last_price=D("100"))

        assert snap.pnl_pct is None
        assert snap.drawdown_pct is None

    def test_daily_pnl_is_change_since_day_start_over_current_invested(self):
        now = BotPnlSnapshot(invested=D("600"), total_pnl=D("-30"), peak_pnl=D("0"))
        start = BotPnlSnapshot(invested=D("600"), total_pnl=D("-10"), peak_pnl=D("0"))

        assert round(daily_pnl_pct(now, start), 4) == D("-3.3333")


class TestPnlAndDrawdownConditions:

    def test_negative_threshold_fires_on_loss_at_or_below(self):
        assert pnl_condition_met(D("-5"), D("-5")) is True
        assert pnl_condition_met(D("-5.5"), D("-5")) is True
        assert pnl_condition_met(D("-4.9"), D("-5")) is False

    def test_positive_threshold_fires_on_gain_at_or_above(self):
        assert pnl_condition_met(D("10"), D("10")) is True
        assert pnl_condition_met(D("9.99"), D("10")) is False

    def test_pnl_none_never_fires(self):
        assert pnl_condition_met(None, D("-5")) is False

    def test_drawdown_fires_at_or_above_threshold(self):
        assert drawdown_condition_met(D("5"), D("5")) is True
        assert drawdown_condition_met(D("4.99"), D("5")) is False
        assert drawdown_condition_met(D("50"), D("0")) is False
        assert drawdown_condition_met(None, D("5")) is False


class TestCooldown:

    NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)

    def test_recent_event_is_in_cooldown(self):
        assert in_cooldown(self.NOW - timedelta(minutes=59), self.NOW, 60) is True

    def test_event_older_than_window_is_not(self):
        assert in_cooldown(self.NOW - timedelta(minutes=60), self.NOW, 60) is False

    def test_naive_db_timestamp_is_treated_as_utc(self):
        naive = (self.NOW - timedelta(minutes=10)).replace(tzinfo=None)
        assert in_cooldown(naive, self.NOW, 60) is True

    def test_no_event_or_zero_minutes_disables_cooldown(self):
        assert in_cooldown(None, self.NOW, 60) is False
        assert in_cooldown(self.NOW, self.NOW, 0) is False
