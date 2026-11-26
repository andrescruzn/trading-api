# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_reconcile_orders_service.py
#
# Tests unitarios del ReconcileOrdersService (órdenes live abiertas).
#
# ESTRATEGIA:
# - Repositorios y LiveExecutor son MagicMock (nunca se llama a ccxt):
#   `live.fetch` devuelve el dict que daría ccxt y el servicio lo traduce
#   con el `LiveExecutor._to_result` real.
# - `utc_now` se fija en el módulo del servicio (ventana y gracia de 10 min).
# - La posición es la entidad real: apply_fill (position_updater) la
#   crea o actualiza vía el position_repo mock.
#
# NOMENCLATURA:
#   test_<condición>_<resultado_esperado>
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.modules.bots.domain.bot_entity import Bot
from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.execution.executor_interface import ExecutionUncertainError
from app.modules.orders.services.execution import reconcile_orders_service as module
from app.modules.orders.services.execution.reconcile_orders_service import (
    ReconcileOrdersService,
)

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)


# ======================================================================
# Helpers
# ======================================================================

@pytest.fixture(autouse=True)
def _fixed_now(monkeypatch):
    monkeypatch.setattr(module, "utc_now", lambda: NOW)


def _make_bot() -> Bot:
    return Bot(
        id=1,
        name="Agente live",
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=2,
        feature_set_id=1,
        mode="live",
        status="running",
        risk_params={"risk_pct": 0.01},
    )


def _make_order(
    id: int = 70,
    side: str = "buy",
    type: str = "limit",
    status: str = "sent",
    qty: Decimal = Decimal("1"),
    meta: dict | None = None,
    ts: datetime | None = NOW - timedelta(minutes=30),
    exchange_order_id: str | None = "ex-70",
    signal_id: int | None = None,
) -> Order:
    return Order(
        id=id,
        bot_id=1,
        side=side,
        type=type,
        qty=qty,
        status=status,
        exchange_order_id=exchange_order_id,
        price=Decimal("100"),
        meta=meta if meta is not None else {"symbol": "BTC/USDT", "mode": "live"},
        ts=ts,
        client_order_id=f"ta-{id}",
        signal_id=signal_id,
    )


def _remote(status: str = "closed", filled=1, average=100, fee_cost=0.1, id: str = "ex-70") -> dict:
    return {
        "id": id,
        "status": status,
        "filled": filled,
        "average": average,
        "fee": {"cost": fee_cost, "currency": "USDT"},
    }


def _make_service(
    orders: list[Order] | None = None,
    remote=None,
    recorded_fills: list[Fill] | None = None,
    position: Position | None = None,
    bot: Bot | None = None,
    evaluate_alerts: MagicMock | None = None,
    signal_repo: MagicMock | None = None,
    native_stop: MagicMock | None = None,
):
    order_repo = MagicMock()
    order_repo.list_open_live.return_value = orders or []
    order_repo.update.side_effect = lambda o: o

    fill_repo = MagicMock()
    fill_repo.list_by_order.return_value = recorded_fills or []
    fill_repo.create.side_effect = lambda f: f

    position_repo = MagicMock()
    position_repo.get_by_bot_and_symbol.return_value = position
    position_repo.create.side_effect = lambda p: p
    position_repo.update.side_effect = lambda p: p

    bot_repo = MagicMock()
    bot_repo.get_by_id.return_value = bot if bot is not None else _make_bot()

    live = MagicMock()
    # Excepción o lista (una respuesta por orden) → side_effect; dict / None → return_value
    if isinstance(remote, (BaseException, list)):
        live.fetch.side_effect = remote
    else:
        live.fetch.return_value = remote

    service = ReconcileOrdersService(
        order_repo=order_repo,
        fill_repo=fill_repo,
        position_repo=position_repo,
        bot_repo=bot_repo,
        live_executor=live,
        evaluate_alerts=evaluate_alerts,
        signal_repo=signal_repo,
        native_stop=native_stop,
    )
    mocks = {
        "order_repo": order_repo,
        "fill_repo": fill_repo,
        "position_repo": position_repo,
        "live": live,
    }
    return service, mocks


# ======================================================================
# TestRun
# ======================================================================

class TestRun:
    def test_reviews_live_orders_of_last_7_days(self):
        service, mocks = _make_service(orders=[])

        result = service.run(limit=20)

        assert result.success is True
        mocks["order_repo"].list_open_live.assert_called_once_with(
            since=NOW - timedelta(days=7), limit=20
        )
        assert result.data.checked == 0

    def test_exception_in_one_order_rolls_back_and_continues(self):
        first, second = _make_order(id=70), _make_order(id=71)
        service, mocks = _make_service(
            orders=[first, second],
            remote=[ValueError("boom"), _remote(id="ex-71")],
        )

        result = service.run()

        assert result.data.checked == 2
        mocks["order_repo"].rollback.assert_called_once()
        assert [u["order_id"] for u in result.data.updated] == [71]
        assert second.status == "filled"
        mocks["order_repo"].commit.assert_called_once()


# ======================================================================
# TestFills
# ======================================================================

class TestFills:
    def test_late_fill_moves_sent_to_filled_and_applies_fill(self):
        order = _make_order(status="sent")
        service, mocks = _make_service(orders=[order], remote=_remote(filled=1, average=100))

        result = service.run()

        assert order.status == "filled"
        fill = mocks["fill_repo"].create.call_args.args[0]
        assert fill.order_id == 70
        assert fill.qty == Decimal("1")
        assert fill.price == Decimal("100")
        assert fill.fee == Decimal("0.1")
        created = mocks["position_repo"].create.call_args.args[0]
        assert created.qty == Decimal("1")
        assert created.avg_price == Decimal("100")
        mocks["order_repo"].update.assert_called_with(order)
        mocks["order_repo"].commit.assert_called_once()
        assert result.data.updated == [
            {"order_id": 70, "status": "filled", "previous": "sent", "filled": "1"}
        ]

    def test_partial_delta_records_only_new_qty_and_fee_never_negative(self):
        order = _make_order(status="partially_filled")
        recorded = [Fill(id=1, order_id=70, qty=Decimal("0.4"), price=Decimal("100"), fee=Decimal("0.1"))]
        position = Position(id=40, bot_id=1, symbol_id=5, qty=Decimal("0.4"), avg_price=Decimal("100"))
        service, mocks = _make_service(
            orders=[order],
            remote=_remote(status="open", filled=0.6, average=100, fee_cost=0.05),
            recorded_fills=recorded,
            position=position,
        )

        result = service.run()

        fill = mocks["fill_repo"].create.call_args.args[0]
        assert fill.qty == Decimal("0.2")
        assert fill.fee == Decimal("0")
        assert order.status == "partially_filled"
        assert position.qty == Decimal("0.6")
        assert result.data.updated[0]["filled"] == "0.2"

    def test_partial_delta_fee_is_the_difference_when_positive(self):
        order = _make_order(status="partially_filled")
        recorded = [Fill(id=1, order_id=70, qty=Decimal("0.4"), price=Decimal("100"), fee=Decimal("0.1"))]
        service, mocks = _make_service(
            orders=[order],
            remote=_remote(status="open", filled=0.6, average=100, fee_cost=0.15),
            recorded_fills=recorded,
            position=Position(id=40, bot_id=1, symbol_id=5, qty=Decimal("0.4"), avg_price=Decimal("100")),
        )

        service.run()

        fill = mocks["fill_repo"].create.call_args.args[0]
        assert fill.fee == Decimal("0.05")

    def test_no_change_does_not_commit(self):
        order = _make_order(status="sent")
        service, mocks = _make_service(orders=[order], remote=_remote(status="open", filled=0))

        result = service.run()

        assert order.status == "sent"
        assert result.data.updated == []
        mocks["fill_repo"].create.assert_not_called()
        mocks["order_repo"].commit.assert_not_called()

    def test_already_recorded_fill_with_same_status_does_not_commit(self):
        order = _make_order(status="partially_filled")
        recorded = [Fill(id=1, order_id=70, qty=Decimal("0.4"), price=Decimal("100"))]
        service, mocks = _make_service(
            orders=[order],
            remote=_remote(status="open", filled=0.4),
            recorded_fills=recorded,
        )

        result = service.run()

        assert result.data.updated == []
        mocks["order_repo"].commit.assert_not_called()

    def test_partially_filled_then_canceled_remotely_is_canceled(self):
        order = _make_order(status="partially_filled")
        recorded = [Fill(id=1, order_id=70, qty=Decimal("0.4"), price=Decimal("100"))]
        service, mocks = _make_service(
            orders=[order],
            remote=_remote(status="canceled", filled=0.4),
            recorded_fills=recorded,
        )

        result = service.run()

        assert order.status == "canceled"
        mocks["fill_repo"].create.assert_not_called()
        mocks["order_repo"].commit.assert_called_once()
        assert result.data.updated == [
            {"order_id": 70, "status": "canceled", "previous": "partially_filled", "filled": "0"}
        ]

    def test_completes_missing_exchange_order_id(self):
        order = _make_order(status="sent", exchange_order_id=None)
        service, _ = _make_service(orders=[order], remote=_remote(id="ex-new"))

        service.run()

        assert order.exchange_order_id == "ex-new"

    def test_fill_without_price_is_retried_next_cycle(self):
        order = _make_order(status="sent")
        remote = {"id": "ex-70", "status": "closed", "filled": 1, "average": None, "price": None}
        service, mocks = _make_service(orders=[order], remote=remote)

        result = service.run()

        assert order.status == "sent"
        assert result.data.updated == []
        mocks["order_repo"].commit.assert_not_called()


# ======================================================================
# TestUnknownToExchange
# ======================================================================

class TestUnknownToExchange:
    def test_lost_order_older_than_10_min_is_rejected(self):
        order = _make_order(
            status="sent",
            exchange_order_id=None,
            meta={"symbol": "BTC/USDT", "needs_reconciliation": True},
            ts=NOW - timedelta(minutes=11),
        )
        service, mocks = _make_service(orders=[order], remote=None)

        result = service.run()

        assert order.status == "rejected"
        assert order.meta == {"symbol": "BTC/USDT", "error": "La orden no llegó al exchange."}
        mocks["order_repo"].commit.assert_called_once()
        assert result.data.updated == [{"order_id": 70, "status": "rejected", "previous": "sent"}]

    def test_lost_order_younger_than_10_min_is_unchanged(self):
        order = _make_order(
            status="sent",
            exchange_order_id=None,
            meta={"symbol": "BTC/USDT", "needs_reconciliation": True},
            ts=NOW - timedelta(minutes=5),
        )
        service, mocks = _make_service(orders=[order], remote=None)

        result = service.run()

        assert order.status == "sent"
        assert order.meta["needs_reconciliation"] is True
        assert result.data.updated == []
        mocks["order_repo"].commit.assert_not_called()

    def test_unknown_order_without_needs_reconciliation_is_unchanged(self):
        order = _make_order(status="sent", ts=NOW - timedelta(hours=2))
        service, mocks = _make_service(orders=[order], remote=None)

        service.run()

        assert order.status == "sent"
        mocks["order_repo"].commit.assert_not_called()

    def test_naive_ts_from_db_is_treated_as_utc(self):
        naive_ts = (NOW - timedelta(minutes=11)).replace(tzinfo=None)
        order = _make_order(
            status="sent",
            meta={"needs_reconciliation": True},
            ts=naive_ts,
        )
        service, _ = _make_service(orders=[order], remote=None)

        service.run()

        assert order.status == "rejected"

    def test_found_order_clears_needs_reconciliation(self):
        order = _make_order(
            status="sent",
            exchange_order_id=None,
            meta={"symbol": "BTC/USDT", "needs_reconciliation": True},
        )
        service, mocks = _make_service(orders=[order], remote=_remote(status="open", filled=0))

        result = service.run()

        assert "needs_reconciliation" not in order.meta
        assert order.status == "sent"
        mocks["order_repo"].commit.assert_called_once()
        assert result.data.updated[0]["status"] == "sent"


# ======================================================================
# TestExchangeErrors
# ======================================================================

class TestExchangeErrors:
    def test_network_error_is_skipped(self):
        order = _make_order(status="sent")
        service, mocks = _make_service(
            orders=[order], remote=ExecutionUncertainError("timeout")
        )

        result = service.run()

        assert order.status == "sent"
        assert result.data.checked == 1
        assert result.data.updated == []
        mocks["order_repo"].commit.assert_not_called()
        mocks["order_repo"].rollback.assert_not_called()

    def test_exchange_error_is_skipped(self):
        order = _make_order(status="sent")
        service, mocks = _make_service(orders=[order], remote=RuntimeError("bad key"))

        result = service.run()

        assert result.data.updated == []
        mocks["order_repo"].commit.assert_not_called()

    def test_missing_bot_is_skipped(self):
        order = _make_order(status="sent")
        service, mocks = _make_service(orders=[order], remote=_remote())
        service._bot_repo.get_by_id.return_value = None

        result = service.run()

        mocks["live"].fetch.assert_not_called()
        assert result.data.updated == []


# ======================================================================
# TestNativeStopLoss
# ======================================================================

class TestNativeStopLoss:
    def test_native_stop_filled_leaves_position_flat_and_unlinked(self):
        stop = _make_order(id=77, side="sell", type="stop", status="sent", exchange_order_id="ex-77")
        position = Position(
            id=40, bot_id=1, symbol_id=5, qty=Decimal("1"), avg_price=Decimal("100"),
            stop_loss=Decimal("90"), take_profit=Decimal("130"), signal_id=11, sl_order_id=77,
        )
        service, _ = _make_service(
            orders=[stop], remote=_remote(id="ex-77", filled=1, average=90), position=position
        )

        service.run()

        assert stop.status == "filled"
        assert position.is_flat()
        assert position.sl_order_id is None
        assert position.realized_pnl == Decimal("-10")

    def test_native_stop_canceled_remotely_unlinks_position(self):
        stop = _make_order(id=77, side="sell", type="stop", status="sent", exchange_order_id="ex-77")
        position = Position(
            id=40, bot_id=1, symbol_id=5, qty=Decimal("1"), avg_price=Decimal("100"),
            stop_loss=Decimal("90"), take_profit=Decimal("130"), signal_id=11, sl_order_id=77,
        )
        service, mocks = _make_service(
            orders=[stop], remote=_remote(id="ex-77", status="canceled", filled=0), position=position
        )

        service.run()

        assert stop.status == "canceled"
        assert position.sl_order_id is None
        assert position.qty == Decimal("1")
        assert position.stop_loss == Decimal("90")
        mocks["position_repo"].update.assert_called_with(position)

    def test_open_native_stop_keeps_link(self):
        stop = _make_order(
            id=77, side="sell", type="stop", status="sent",
            meta={"needs_reconciliation": True},
        )
        position = Position(
            id=40, bot_id=1, symbol_id=5, qty=Decimal("1"), avg_price=Decimal("100"), sl_order_id=77,
        )
        service, _ = _make_service(
            orders=[stop], remote=_remote(id="ex-77", status="open", filled=0), position=position
        )

        service.run()

        assert position.sl_order_id == 77

    def test_other_order_finishing_does_not_unlink_native_stop(self):
        order = _make_order(id=70, status="sent")
        position = Position(
            id=40, bot_id=1, symbol_id=5, qty=Decimal("1"), avg_price=Decimal("100"), sl_order_id=77,
        )
        service, _ = _make_service(orders=[order], remote=_remote(), position=position)

        service.run()

        assert position.sl_order_id == 77


# ======================================================================
# TestAlerts
# ======================================================================

class TestAlerts:
    def test_rejected_order_calls_alert_hook(self):
        order = _make_order(status="sent")
        alerts = MagicMock()
        service, _ = _make_service(
            orders=[order], remote=_remote(status="rejected", filled=0), evaluate_alerts=alerts
        )

        service.run()

        assert order.status == "rejected"
        alerts.evaluate_order_alerts.assert_called_once_with(order=order, bot_id=1)

    def test_lost_order_rejected_calls_alert_hook(self):
        order = _make_order(
            status="sent", meta={"needs_reconciliation": True}, ts=NOW - timedelta(minutes=15)
        )
        alerts = MagicMock()
        service, _ = _make_service(orders=[order], remote=None, evaluate_alerts=alerts)

        service.run()

        alerts.evaluate_order_alerts.assert_called_once_with(order=order, bot_id=1)

    def test_filled_order_does_not_call_alert_hook(self):
        order = _make_order(status="sent")
        alerts = MagicMock()
        service, _ = _make_service(orders=[order], remote=_remote(), evaluate_alerts=alerts)

        service.run()

        alerts.evaluate_order_alerts.assert_not_called()

    def test_alert_hook_error_does_not_break_reconciliation(self):
        order = _make_order(status="sent")
        alerts = MagicMock()
        alerts.evaluate_order_alerts.side_effect = RuntimeError("smtp down")
        service, mocks = _make_service(
            orders=[order], remote=_remote(status="rejected", filled=0), evaluate_alerts=alerts
        )

        result = service.run()

        assert result.data.updated[0]["status"] == "rejected"
        mocks["order_repo"].rollback.assert_not_called()


# ======================================================================
# TestSyncOne
# ======================================================================

class TestSyncOne:
    def test_sync_one_applies_same_logic_to_a_single_order(self):
        order = _make_order(status="sent")
        service, mocks = _make_service(remote=_remote(filled=1, average=100))

        change = service.sync_one(order)

        assert change == {"status": "filled", "previous": "sent", "filled": "1"}
        assert order.status == "filled"
        mocks["fill_repo"].create.assert_called_once()
        mocks["order_repo"].commit.assert_called_once()
        mocks["order_repo"].list_open_live.assert_not_called()

    def test_sync_one_returns_none_without_changes(self):
        order = _make_order(status="sent")
        service, mocks = _make_service(remote=_remote(status="open", filled=0))

        assert service.sync_one(order) is None
        mocks["order_repo"].commit.assert_not_called()

    def test_sync_one_returns_none_on_network_error(self):
        order = _make_order(status="sent")
        service, _ = _make_service(remote=ExecutionUncertainError("timeout"))

        assert service.sync_one(order) is None

    def test_sync_one_uses_utc_now_for_lost_orders(self):
        order = _make_order(
            status="sent", meta={"needs_reconciliation": True}, ts=NOW - timedelta(minutes=11)
        )
        service, _ = _make_service(remote=None)

        change = service.sync_one(order)

        assert change == {"status": "rejected", "previous": "sent"}


# ======================================================================
# TestPendingProtection
# ======================================================================

_PROTECTION = {"stop_loss": "90", "take_profit": "120"}


def _protected_buy(protection: dict | None = None, signal_id: int | None = 11) -> Order:
    return _make_order(
        status="sent",
        type="market",
        meta={"symbol": "BTC/USDT", "mode": "live", "protection": dict(protection or _PROTECTION)},
        signal_id=signal_id,
    )


def _native_stop_ok() -> MagicMock:
    native_stop = MagicMock()
    native_stop.place.return_value = MagicMock(success=True)
    return native_stop


class TestPendingProtection:
    """SL/TP que la compra traía y se aplican cuando el exchange la ejecuta."""

    def test_late_fill_applies_pending_protection_to_new_position(self):
        order = _protected_buy()
        service, mocks = _make_service(orders=[order], remote=_remote(filled=1, average=100))

        service.run()

        position = mocks["position_repo"].create.call_args.args[0]
        assert position.stop_loss == Decimal("90")
        assert position.take_profit == Decimal("120")
        assert position.signal_id == 11
        mocks["position_repo"].update.assert_called_with(position)

    def test_applied_flag_is_stored_in_order_meta(self):
        order = _protected_buy()
        service, mocks = _make_service(orders=[order], remote=_remote(filled=1, average=100))

        service.run()

        assert order.meta["protection"] == {**_PROTECTION, "applied": True}
        mocks["order_repo"].update.assert_called_with(order)
        # Fill, estado final y protección en UN solo commit: si la protección
        # fuera aparte y fallara, la orden final ya no se volvería a revisar
        assert mocks["order_repo"].commit.call_count == 1

    def test_protection_is_set_before_the_commit(self):
        order = _protected_buy()
        service, mocks = _make_service(orders=[order], remote=_remote(filled=1, average=100))
        seen_at_commit = {}

        def _commit():
            position = mocks["position_repo"].create.call_args.args[0]
            seen_at_commit["stop_loss"] = position.stop_loss
            seen_at_commit["applied"] = order.meta["protection"].get("applied")

        mocks["order_repo"].commit.side_effect = _commit

        service.run()

        assert seen_at_commit == {"stop_loss": Decimal("90"), "applied": True}

    def test_missing_side_keeps_existing_position_levels(self):
        order = _protected_buy(protection={"stop_loss": None, "take_profit": "120"}, signal_id=None)
        position = Position(
            id=40, bot_id=1, symbol_id=5, qty=Decimal("1"), avg_price=Decimal("100"),
            stop_loss=Decimal("85"), take_profit=Decimal("140"), signal_id=3,
        )
        service, _ = _make_service(
            orders=[order], remote=_remote(filled=1, average=100), position=position
        )

        service.run()

        assert position.stop_loss == Decimal("85")
        assert position.take_profit == Decimal("120")
        assert position.signal_id == 3

    def test_live_bot_places_native_stop_with_pending_stop_loss(self):
        order = _protected_buy()
        bot = _make_bot()
        native_stop = _native_stop_ok()
        service, mocks = _make_service(
            orders=[order], remote=_remote(filled=1, average=100), bot=bot, native_stop=native_stop
        )

        service.run()

        position = mocks["position_repo"].create.call_args.args[0]
        native_stop.place.assert_called_once_with(bot, position, Decimal("90"))

    def test_paper_bot_does_not_place_native_stop(self):
        order = _protected_buy()
        bot = _make_bot()
        bot.mode = "paper"
        native_stop = _native_stop_ok()
        service, mocks = _make_service(
            orders=[order], remote=_remote(filled=1, average=100), bot=bot, native_stop=native_stop
        )

        service.run()

        native_stop.place.assert_not_called()
        position = mocks["position_repo"].create.call_args.args[0]
        assert position.stop_loss == Decimal("90")

    def test_position_with_native_stop_does_not_place_another(self):
        order = _protected_buy()
        position = Position(
            id=40, bot_id=1, symbol_id=5, qty=Decimal("1"), avg_price=Decimal("100"), sl_order_id=77,
        )
        native_stop = _native_stop_ok()
        service, _ = _make_service(
            orders=[order], remote=_remote(filled=1, average=100),
            position=position, native_stop=native_stop,
        )

        service.run()

        native_stop.place.assert_not_called()
        assert position.sl_order_id == 77

    def test_take_profit_only_does_not_place_native_stop(self):
        order = _protected_buy(protection={"stop_loss": None, "take_profit": "120"})
        native_stop = _native_stop_ok()
        service, _ = _make_service(
            orders=[order], remote=_remote(filled=1, average=100), native_stop=native_stop
        )

        service.run()

        native_stop.place.assert_not_called()

    def test_native_stop_failure_does_not_break_reconciliation(self):
        order = _protected_buy()
        native_stop = MagicMock()
        native_stop.place.return_value = MagicMock(
            success=False, error=MagicMock(code="NATIVE_STOP_FAILED")
        )
        service, mocks = _make_service(
            orders=[order], remote=_remote(filled=1, average=100), native_stop=native_stop
        )

        result = service.run()

        assert result.data.updated[0]["status"] == "filled"
        mocks["order_repo"].rollback.assert_not_called()

    def test_already_applied_protection_is_not_applied_again(self):
        order = _protected_buy(protection={**_PROTECTION, "applied": True})
        native_stop = _native_stop_ok()
        service, mocks = _make_service(
            orders=[order], remote=_remote(filled=1, average=100), native_stop=native_stop
        )

        service.run()

        position = mocks["position_repo"].create.call_args.args[0]
        assert position.stop_loss is None
        assert position.take_profit is None
        native_stop.place.assert_not_called()
        mocks["order_repo"].commit.assert_called_once()

    def test_sell_order_never_applies_protection(self):
        order = _protected_buy()
        order.side = "sell"
        position = Position(id=40, bot_id=1, symbol_id=5, qty=Decimal("2"), avg_price=Decimal("100"))
        native_stop = _native_stop_ok()
        service, _ = _make_service(
            orders=[order], remote=_remote(filled=1, average=110),
            position=position, native_stop=native_stop,
        )

        service.run()

        assert position.qty == Decimal("1")
        assert position.stop_loss is None
        assert "applied" not in order.meta["protection"]
        native_stop.place.assert_not_called()

    def test_without_new_fill_protection_stays_pending(self):
        order = _protected_buy()
        order.meta["needs_reconciliation"] = True
        service, mocks = _make_service(orders=[order], remote=_remote(status="open", filled=0))

        service.run()

        assert "applied" not in order.meta["protection"]
        mocks["position_repo"].update.assert_not_called()


# ======================================================================
# TestSettleSignal
# ======================================================================

def _signal_repo(transitioned: bool = True) -> MagicMock:
    repo = MagicMock()
    repo.transition_decision.return_value = transitioned
    return repo


class TestSettleSignal:
    """La decisión de la señal cuya orden quedó `sent` se cierra al reconciliarla."""

    def test_filled_order_marks_signal_executed(self):
        order = _make_order(status="sent", signal_id=11)
        signal_repo = _signal_repo()
        service, _ = _make_service(orders=[order], remote=_remote(), signal_repo=signal_repo)

        service.run()

        signal_repo.transition_decision.assert_called_once_with(
            11, from_statuses=("executing",), to_status="executed"
        )
        signal_repo.commit.assert_called_once()

    def test_partially_filled_order_marks_signal_executed(self):
        order = _make_order(status="sent", signal_id=11)
        signal_repo = _signal_repo()
        service, _ = _make_service(
            orders=[order], remote=_remote(status="open", filled=0.5), signal_repo=signal_repo
        )

        service.run()

        assert order.status == "partially_filled"
        assert signal_repo.transition_decision.call_args.kwargs["to_status"] == "executed"

    def test_rejected_order_marks_signal_failed(self):
        order = _make_order(status="sent", signal_id=11)
        signal_repo = _signal_repo()
        service, _ = _make_service(
            orders=[order], remote=_remote(status="rejected", filled=0), signal_repo=signal_repo
        )

        service.run()

        signal_repo.transition_decision.assert_called_once_with(
            11,
            from_statuses=("executing",),
            to_status="failed",
            decision_reason="ORDER_EXECUTION_FAILED",
        )
        signal_repo.commit.assert_called_once()

    def test_lost_order_marks_signal_failed(self):
        order = _make_order(
            status="sent", signal_id=11,
            meta={"needs_reconciliation": True}, ts=NOW - timedelta(minutes=11),
        )
        signal_repo = _signal_repo()
        service, _ = _make_service(orders=[order], remote=None, signal_repo=signal_repo)

        service.run()

        assert signal_repo.transition_decision.call_args.kwargs["to_status"] == "failed"

    def test_canceled_order_with_fills_marks_signal_executed(self):
        order = _make_order(status="partially_filled", signal_id=11)
        recorded = [Fill(id=1, order_id=70, qty=Decimal("0.4"), price=Decimal("100"))]
        signal_repo = _signal_repo()
        service, _ = _make_service(
            orders=[order], remote=_remote(status="canceled", filled=0.4),
            recorded_fills=recorded, signal_repo=signal_repo,
        )

        service.run()

        assert order.status == "canceled"
        signal_repo.transition_decision.assert_called_once_with(
            11, from_statuses=("executing",), to_status="executed"
        )

    def test_canceled_order_without_fills_marks_signal_failed(self):
        order = _make_order(status="sent", signal_id=11)
        signal_repo = _signal_repo()
        service, _ = _make_service(
            orders=[order], remote=_remote(status="canceled", filled=0), signal_repo=signal_repo
        )

        service.run()

        assert order.status == "canceled"
        signal_repo.transition_decision.assert_called_once_with(
            11,
            from_statuses=("executing",),
            to_status="failed",
            decision_reason="ORDER_EXECUTION_FAILED",
        )

    def test_still_open_order_does_not_settle_signal(self):
        order = _make_order(status="sent", signal_id=11, meta={"needs_reconciliation": True})
        signal_repo = _signal_repo()
        service, _ = _make_service(
            orders=[order], remote=_remote(status="open", filled=0), signal_repo=signal_repo
        )

        service.run()

        signal_repo.transition_decision.assert_not_called()

    def test_no_commit_when_signal_was_not_executing(self):
        order = _make_order(status="sent", signal_id=11)
        signal_repo = _signal_repo(transitioned=False)
        service, _ = _make_service(orders=[order], remote=_remote(), signal_repo=signal_repo)

        service.run()

        signal_repo.transition_decision.assert_called_once()
        signal_repo.commit.assert_not_called()

    def test_order_without_signal_does_not_touch_signals(self):
        order = _make_order(status="sent", signal_id=None)
        signal_repo = _signal_repo()
        service, _ = _make_service(orders=[order], remote=_remote(), signal_repo=signal_repo)

        service.run()

        signal_repo.transition_decision.assert_not_called()
        signal_repo.commit.assert_not_called()

    def test_without_signal_repo_reconciles_normally(self):
        order = _make_order(status="sent", signal_id=11)
        service, _ = _make_service(orders=[order], remote=_remote(), signal_repo=None)

        result = service.run()

        assert order.status == "filled"
        assert result.data.updated[0]["status"] == "filled"
