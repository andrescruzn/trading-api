# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_cancel_order_service.py
#
# Tests unitarios del CancelOrderService.
#
# ESTRATEGIA:
# - OrderRepository, BotRepository, AccountRepository, LiveExecutor y
#   ReconcileOrdersService son MagicMock (sin BD ni exchange).
# - Order y Bot son entidades reales.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.modules.bots.domain.bot_entity import Bot
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.execution.executor_interface import ExecutionUncertainError
from app.modules.orders.services.orders.cancel_order_service import CancelOrderService


# ======================================================================
# Helpers
# ======================================================================

def _make_bot(mode: str = "live") -> Bot:
    return Bot(
        id=1,
        name="Agente de prueba",
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=2,
        feature_set_id=1,
        mode=mode,
        status="running",
        risk_params={"risk_pct": 0.01},
    )


def _make_order(
    status: str = "sent",
    mode: str | None = "live",
    exchange_order_id: str | None = "ex-123",
) -> Order:
    meta = {"symbol": "BTC/USDT", "reason": "manual"}
    if mode is not None:
        meta["mode"] = mode
    return Order(
        id=10,
        bot_id=1,
        side="buy",
        type="limit",
        qty=Decimal("1"),
        status=status,
        price=Decimal("95"),
        exchange_order_id=exchange_order_id,
        client_order_id="ta-10",
        meta=meta,
    )


def _make_service(
    order: Order | None = None,
    bot: Bot | None = None,
    cancel_error: Exception | None = None,
    sync_change: dict | None = None,
):
    order_repo = MagicMock()
    order_repo.get_by_id.return_value = order
    order_repo.update.side_effect = lambda o: o

    bot_repo = MagicMock()
    bot_repo.get_by_id.return_value = bot

    account_repo = MagicMock()
    account_repo.get_by_id.return_value = SimpleNamespace(id=2, user_id=7)

    live = MagicMock()
    if cancel_error is not None:
        live.cancel.side_effect = cancel_error
    else:
        live.cancel.return_value = True

    reconcile = MagicMock()
    reconcile.sync_one.return_value = sync_change

    service = CancelOrderService(
        order_repo=order_repo,
        bot_repo=bot_repo,
        account_repo=account_repo,
        live_executor=live,
        reconcile=reconcile,
    )
    mocks = SimpleNamespace(
        order_repo=order_repo,
        bot_repo=bot_repo,
        account_repo=account_repo,
        live=live,
        reconcile=reconcile,
    )
    return service, mocks


def _assert_nothing_sent(mocks) -> None:
    mocks.live.cancel.assert_not_called()
    mocks.reconcile.sync_one.assert_not_called()
    mocks.order_repo.commit.assert_not_called()


# ======================================================================
# TestOrderNotFound
# ======================================================================

class TestOrderNotFound:
    def test_missing_order_returns_not_found(self):
        service, mocks = _make_service(order=None, bot=_make_bot())

        result = service.cancel(order_id=10, owner_id=7)

        assert result.success is False
        assert result.error.code == "ORDER_NOT_FOUND"
        assert result.error.http_status == 404
        _assert_nothing_sent(mocks)

    def test_order_of_foreign_bot_returns_not_found(self):
        service, mocks = _make_service(order=_make_order(), bot=_make_bot())

        result = service.cancel(order_id=10, owner_id=99)

        assert result.error.code == "ORDER_NOT_FOUND"
        assert result.error.http_status == 404
        _assert_nothing_sent(mocks)

    def test_order_whose_bot_was_deleted_returns_not_found(self):
        service, mocks = _make_service(order=_make_order(), bot=None)

        result = service.cancel(order_id=10, owner_id=None)

        assert result.error.code == "ORDER_NOT_FOUND"
        _assert_nothing_sent(mocks)

    def test_admin_can_cancel_any_bot_order(self):
        service, mocks = _make_service(order=_make_order(), bot=_make_bot())

        result = service.cancel(order_id=10, owner_id=None)

        assert result.success is True
        mocks.account_repo.get_by_id.assert_not_called()


# ======================================================================
# TestNotCancelable
# ======================================================================

class TestNotCancelable:
    @pytest.mark.parametrize("status", ["new", "filled", "canceled", "rejected"])
    def test_non_open_status_returns_not_cancelable(self, status):
        service, mocks = _make_service(order=_make_order(status=status), bot=_make_bot())

        result = service.cancel(order_id=10, owner_id=7)

        assert result.error.code == "ORDER_NOT_CANCELABLE"
        assert result.error.http_status == 409
        assert result.error.meta == {"status": status}
        _assert_nothing_sent(mocks)

    def test_paper_order_returns_not_cancelable(self):
        service, mocks = _make_service(
            order=_make_order(mode="paper"), bot=_make_bot(mode="live")
        )

        result = service.cancel(order_id=10, owner_id=7)

        assert result.error.code == "ORDER_NOT_CANCELABLE"
        _assert_nothing_sent(mocks)

    def test_order_without_mode_falls_back_to_paper_bot_mode(self):
        service, mocks = _make_service(
            order=_make_order(mode=None), bot=_make_bot(mode="paper")
        )

        result = service.cancel(order_id=10, owner_id=7)

        assert result.error.code == "ORDER_NOT_CANCELABLE"
        _assert_nothing_sent(mocks)

    def test_order_without_exchange_id_returns_pending_sync(self):
        service, mocks = _make_service(
            order=_make_order(exchange_order_id=None), bot=_make_bot()
        )

        result = service.cancel(order_id=10, owner_id=7)

        assert result.error.code == "ORDER_CANCEL_PENDING_SYNC"
        assert result.error.http_status == 409
        _assert_nothing_sent(mocks)


# ======================================================================
# TestExchangeErrors
# ======================================================================

class TestExchangeErrors:
    def test_uncertain_error_returns_cancel_uncertain(self):
        service, mocks = _make_service(
            order=_make_order(), bot=_make_bot(), cancel_error=ExecutionUncertainError("timeout")
        )

        result = service.cancel(order_id=10, owner_id=7)

        assert result.error.code == "ORDER_CANCEL_UNCERTAIN"
        assert result.error.http_status == 502
        assert result.error.meta == {"order_id": 10}
        mocks.reconcile.sync_one.assert_not_called()
        mocks.order_repo.commit.assert_not_called()

    def test_runtime_error_returns_cancel_failed(self):
        service, mocks = _make_service(
            order=_make_order(), bot=_make_bot(), cancel_error=RuntimeError("unknown order")
        )

        result = service.cancel(order_id=10, owner_id=7)

        assert result.error.code == "ORDER_CANCEL_FAILED"
        assert result.error.http_status == 502
        assert result.error.meta == {"order_id": 10}
        mocks.reconcile.sync_one.assert_not_called()
        mocks.order_repo.commit.assert_not_called()


# ======================================================================
# TestCancelSuccess
# ======================================================================

class TestCancelSuccess:
    @pytest.mark.parametrize("status", ["sent", "partially_filled"])
    def test_cancels_on_exchange_and_syncs_order(self, status):
        order = _make_order(status=status)
        bot = _make_bot()
        service, mocks = _make_service(order=order, bot=bot)

        result = service.cancel(order_id=10, owner_id=7)

        assert result.success is True
        mocks.live.cancel.assert_called_once_with(order, bot)
        mocks.reconcile.sync_one.assert_called_once_with(order)

    def test_sync_without_change_marks_cancel_requested_and_commits(self):
        order = _make_order(status="sent")
        service, mocks = _make_service(order=order, bot=_make_bot(), sync_change=None)

        result = service.cancel(order_id=10, owner_id=7)

        assert result.success is True
        assert result.data.meta["cancel_requested"] is True
        assert result.data.meta["symbol"] == "BTC/USDT"
        mocks.order_repo.update.assert_called_once_with(order)
        mocks.order_repo.commit.assert_called_once()

    def test_sync_with_change_does_not_commit_again(self):
        order = _make_order(status="sent")
        service, mocks = _make_service(order=order, bot=_make_bot())

        def _sync(o):
            o.status = "canceled"
            return {"order_id": o.id, "status": "canceled"}

        mocks.reconcile.sync_one.side_effect = _sync

        result = service.cancel(order_id=10, owner_id=7)

        assert result.success is True
        assert result.data.status == "canceled"
        assert "cancel_requested" not in result.data.meta
        mocks.order_repo.update.assert_not_called()
        mocks.order_repo.commit.assert_not_called()

    def test_sync_without_change_but_final_status_does_not_mark_cancel_requested(self):
        order = _make_order(status="sent")
        service, mocks = _make_service(order=order, bot=_make_bot())

        def _sync(o):
            o.status = "canceled"
            return None

        mocks.reconcile.sync_one.side_effect = _sync

        result = service.cancel(order_id=10, owner_id=7)

        assert result.success is True
        assert "cancel_requested" not in result.data.meta
        mocks.order_repo.commit.assert_not_called()
