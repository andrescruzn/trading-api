# -*- coding: utf-8 -*-

# ======================================================================
# tests/alerts/test_evaluate_periodic_alerts_service.py
#
# EvaluatePeriodicAlertsService con repositorios MagicMock (sin BD):
# precio (ambos sentidos), P&L total y diario, drawdown, antispam y
# aislamiento de errores por regla.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.modules.alerts.domain.alert_rule_entity import AlertRule
from app.modules.alerts.services.evaluation import EvaluatePeriodicAlertsService
from app.modules.orders.domain.performance import TradeFill

# 15:00 UTC = 10:00 en Bogotá → el día empezó a las 05:00 UTC
NOW = datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc)
DAY_START = datetime(2026, 10, 20, 5, 0, tzinfo=timezone.utc)

BOT = SimpleNamespace(id=7, name="Oro — tendencia 4h", symbol_id=3, timeframe_id=2)
SYMBOL = SimpleNamespace(id=3, symbol="BTC/USDT", quote_asset="USDT")


def _rule(rule_type: str, spec: dict, rule_id: int = 1, bot_id: int | None = None) -> AlertRule:
    return AlertRule(
        id=rule_id, name=f"Regla {rule_id}", rule_type=rule_type, rule_spec=spec,
        channels={"desktop": True}, user_id=5, bot_id=bot_id,
    )


def _candle(close: str, ts: datetime) -> SimpleNamespace:
    return SimpleNamespace(close=D(close), ts=ts)


def _make_service(
    rules: dict[str, list[AlertRule]],
    *,
    last_event_ts: datetime | None = None,
    fills: list[TradeFill] | None = None,
    candles_by_tf: dict[int, list] | None = None,
    bot_candles=None,
    repeat_minutes: int = 60,
):
    rule_repo = MagicMock()
    rule_repo.list_active_by_type_and_bot.side_effect = (
        lambda rule_type, bot_id=None: rules.get(rule_type, [])
    )

    event_repo = MagicMock()
    event_repo.get_last_by_rule.return_value = (
        SimpleNamespace(ts=last_event_ts) if last_event_ts else None
    )

    fire = MagicMock()

    timeframe_repo = MagicMock()
    timeframe_repo.list_all.return_value = [SimpleNamespace(id=1), SimpleNamespace(id=2)]

    candles_by_tf = candles_by_tf or {}

    def list_candles(symbol_id, timeframe_id, from_ts=None, to_ts=None, limit=500):
        if bot_candles is not None and symbol_id == BOT.symbol_id and timeframe_id == BOT.timeframe_id:
            return bot_candles(to_ts)
        return candles_by_tf.get(timeframe_id, [])

    candle_repo = MagicMock()
    candle_repo.list_candles.side_effect = list_candles

    symbol_repo = MagicMock()
    symbol_repo.get_by_id.return_value = SYMBOL

    bot_repo = MagicMock()
    bot_repo.get_by_id.side_effect = lambda bot_id: BOT if bot_id == BOT.id else None

    fill_repo = MagicMock()
    fill_repo.list_trade_fills_by_bots.side_effect = lambda ids: {i: list(fills or []) for i in ids}

    service = EvaluatePeriodicAlertsService(
        rule_repo=rule_repo,
        event_repo=event_repo,
        fire_service=fire,
        candle_repo=candle_repo,
        timeframe_repo=timeframe_repo,
        symbol_repo=symbol_repo,
        bot_repo=bot_repo,
        fill_repo=fill_repo,
        repeat_minutes=repeat_minutes,
        clock=lambda: NOW,
    )
    return service, fire, rule_repo


def _buy_yesterday() -> list[TradeFill]:
    """Compra abierta de 0,01 BTC a 60.000 (costo 600) hecha ayer."""
    return [TradeFill("buy", D("0.01"), D("60000"), D("0"), NOW - timedelta(days=1))]


def _bot_candles(day_start_close: str, last_close: str):
    def load(to_ts):
        if to_ts is not None and to_ts < DAY_START:
            return [_candle(day_start_close, DAY_START - timedelta(hours=4))]
        return [_candle(last_close, NOW - timedelta(minutes=5))]
    return load


# ======================================================================
# Precio
# ======================================================================

class TestPriceRules:

    # tf 1 tiene la vela más reciente: manda su cierre
    CANDLES = {
        1: [_candle("79500", NOW - timedelta(minutes=1))],
        2: [_candle("81000", NOW - timedelta(hours=1))],
    }

    def test_fires_when_last_close_is_below_threshold(self):
        rule = _rule("price", {"symbol_id": 3, "operator": "lt", "threshold": 80000})
        svc, fire, _ = _make_service({"price": [rule]}, candles_by_tf=self.CANDLES)

        report = svc.run().data

        assert report.fired == 1
        kwargs = fire.fire.call_args.kwargs
        assert kwargs["rule"] is rule
        assert kwargs["title"] == "BTC/USDT por debajo de 80.000,00 USDT"
        assert kwargs["payload"]["current_price"] == 79500.0
        assert kwargs["severity"] == "warning"

    def test_fires_when_last_close_is_above_threshold(self):
        rule = _rule("price", {"symbol_id": 3, "operator": "gt", "threshold": 79000})
        svc, fire, _ = _make_service({"price": [rule]}, candles_by_tf=self.CANDLES)

        assert svc.run().data.fired == 1
        assert fire.fire.call_args.kwargs["title"].startswith("BTC/USDT por encima de")

    def test_does_not_fire_when_condition_is_false(self):
        rule = _rule("price", {"symbol_id": 3, "operator": "gt", "threshold": 80000})
        svc, fire, _ = _make_service({"price": [rule]}, candles_by_tf=self.CANDLES)

        report = svc.run().data

        assert report.fired == 0 and report.checked == 1
        fire.fire.assert_not_called()

    def test_without_candles_the_rule_is_skipped(self):
        rule = _rule("price", {"symbol_id": 3, "operator": "lt", "threshold": 80000})
        svc, fire, _ = _make_service({"price": [rule]}, candles_by_tf={})

        assert svc.run().data.skipped == 1
        fire.fire.assert_not_called()

    def test_manual_evaluation_uses_given_price_and_symbol(self):
        rule = _rule("price", {"symbol_id": 3, "operator": "lt", "threshold": 80000})
        other = _rule("price", {"symbol_id": 9, "operator": "lt", "threshold": 80000}, rule_id=2)
        svc, fire, _ = _make_service({"price": [rule, other]})

        report = svc.evaluate_price(symbol_id=3, current_price=D("70000")).data

        assert report.checked == 1 and report.fired == 1
        assert fire.fire.call_args.kwargs["payload"]["current_price"] == 70000.0


# ======================================================================
# P&L
# ======================================================================

class TestPnlRules:

    def test_total_pnl_fires_at_minus_5_percent(self):
        # (57.000 − 60.000) × 0,01 = −30 sobre 600 invertidos = −5 %
        rule = _rule("pnl", {"threshold": -5, "period": "total"}, bot_id=7)
        svc, fire, _ = _make_service(
            {"pnl": [rule]}, fills=_buy_yesterday(), bot_candles=_bot_candles("59000", "57000"),
        )

        assert svc.run().data.fired == 1
        kwargs = fire.fire.call_args.kwargs
        assert kwargs["payload"]["pnl_pct"] == -5.0
        assert kwargs["payload"]["invested"] == 600.0
        assert kwargs["title"] == "PnL total -5,00 % · Oro — tendencia 4h"
        assert kwargs["severity"] == "warning"

    def test_daily_pnl_only_counts_since_bogota_midnight(self):
        # Al empezar el día ya iba −10 (cierre 59.000): hoy solo −20 / 600 = −3,33 %
        rule = _rule("pnl", {"threshold": -5, "period": "daily"}, bot_id=7)
        svc, fire, _ = _make_service(
            {"pnl": [rule]}, fills=_buy_yesterday(), bot_candles=_bot_candles("59000", "57000"),
        )

        assert svc.run().data.fired == 0
        fire.fire.assert_not_called()

    def test_daily_pnl_fires_when_today_loss_reaches_threshold(self):
        # Al empezar el día iba en 0 (cierre 60.000): hoy −30 / 600 = −5 %
        rule = _rule("pnl", {"threshold": -5, "period": "daily"}, bot_id=7)
        svc, fire, _ = _make_service(
            {"pnl": [rule]}, fills=_buy_yesterday(), bot_candles=_bot_candles("60000", "57000"),
        )

        assert svc.run().data.fired == 1
        assert fire.fire.call_args.kwargs["title"].startswith("PnL de hoy -5,00 %")

    def test_positive_threshold_fires_on_gain(self):
        # (63.000 − 60.000) × 0,01 = +30 → +5 %
        rule = _rule("pnl", {"threshold": 5, "period": "total"}, bot_id=7)
        svc, fire, _ = _make_service(
            {"pnl": [rule]}, fills=_buy_yesterday(), bot_candles=_bot_candles("60000", "63000"),
        )

        assert svc.run().data.fired == 1
        assert fire.fire.call_args.kwargs["severity"] == "info"

    def test_rule_without_bot_is_skipped(self):
        rule = _rule("pnl", {"threshold": -5, "period": "total"}, bot_id=None)
        svc, fire, _ = _make_service({"pnl": [rule]}, fills=_buy_yesterday())

        assert svc.run().data.skipped == 1
        fire.fire.assert_not_called()

    def test_bot_without_trades_is_skipped(self):
        rule = _rule("pnl", {"threshold": -5, "period": "total"}, bot_id=7)
        svc, fire, _ = _make_service(
            {"pnl": [rule]}, fills=[], bot_candles=_bot_candles("60000", "57000"),
        )

        assert svc.run().data.skipped == 1


# ======================================================================
# Drawdown
# ======================================================================

class TestDrawdownRules:

    def _fills(self) -> list[TradeFill]:
        t = NOW - timedelta(days=3)
        return [
            TradeFill("buy", D("1"), D("1000"), D("0"), t),
            TradeFill("sell", D("1"), D("1040"), D("0"), t + timedelta(hours=1)),    # +40
            TradeFill("buy", D("1"), D("800"), D("0"), t + timedelta(hours=2)),
            TradeFill("sell", D("1"), D("780"), D("0"), t + timedelta(hours=3)),     # −20
            TradeFill("buy", D("0.01"), D("60000"), D("0"), t + timedelta(hours=4)),  # abierta
        ]

    def test_fires_when_drawdown_from_peak_reaches_threshold(self):
        # pico +40, ahora 40 − 20 − 30 = −10 → caída 50 / 1.000 = 5 %
        rule = _rule("drawdown", {"threshold": 5}, bot_id=7)
        svc, fire, _ = _make_service(
            {"drawdown": [rule]}, fills=self._fills(), bot_candles=_bot_candles("57000", "57000"),
        )

        assert svc.run().data.fired == 1
        kwargs = fire.fire.call_args.kwargs
        assert kwargs["payload"]["drawdown_pct"] == 5.0
        assert kwargs["payload"]["drawdown"] == 50.0
        assert kwargs["severity"] == "critical"

    def test_does_not_fire_below_threshold(self):
        # Último cierre 59.000: ahora +10 → caída 30 / 1.000 = 3 %
        rule = _rule("drawdown", {"threshold": 5}, bot_id=7)
        svc, fire, _ = _make_service(
            {"drawdown": [rule]}, fills=self._fills(), bot_candles=_bot_candles("59000", "59000"),
        )

        assert svc.run().data.fired == 0
        fire.fire.assert_not_called()


# ======================================================================
# Antispam y errores
# ======================================================================

class TestCooldownAndIsolation:

    CANDLES = {1: [_candle("79500", NOW - timedelta(minutes=1))]}

    def _price_rule(self, rule_id: int = 1) -> AlertRule:
        return _rule("price", {"symbol_id": 3, "operator": "lt", "threshold": 80000}, rule_id=rule_id)

    def test_rule_that_fired_recently_is_not_refired(self):
        svc, fire, _ = _make_service(
            {"price": [self._price_rule()]},
            candles_by_tf=self.CANDLES,
            last_event_ts=NOW - timedelta(minutes=30),
        )

        report = svc.run().data

        assert report.cooldown == 1 and report.fired == 0
        fire.fire.assert_not_called()

    def test_rule_fires_again_after_the_window(self):
        svc, fire, _ = _make_service(
            {"price": [self._price_rule()]},
            candles_by_tf=self.CANDLES,
            last_event_ts=NOW - timedelta(minutes=61),
        )

        assert svc.run().data.fired == 1

    def test_zero_minutes_fires_every_cycle(self):
        svc, _, _ = _make_service(
            {"price": [self._price_rule()]},
            candles_by_tf=self.CANDLES,
            last_event_ts=NOW - timedelta(seconds=30),
            repeat_minutes=0,
        )

        assert svc.run().data.fired == 1

    def test_error_in_one_rule_does_not_stop_the_others(self):
        svc, fire, rule_repo = _make_service(
            {"price": [self._price_rule(1), self._price_rule(2)]}, candles_by_tf=self.CANDLES,
        )
        fire.fire.side_effect = [RuntimeError("canal caído"), MagicMock()]

        report = svc.run().data

        assert report.failed == 1 and report.fired == 1
        assert fire.fire.call_count == 2
        rule_repo.rollback.assert_called_once()
