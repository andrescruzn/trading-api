# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_protect_positions_service.py
#
# Tests unitarios del ProtectPositionsService (cierre por SL / TP).
#
# ESTRATEGIA:
# - Repositorios y CreateOrderService son MagicMock; la posición es la
#   entidad real (su protection_hit decide qué nivel se tocó).
# - La vela es un MagicMock con low / high.
#
# NOMENCLATURA:
#   test_<condición>_<resultado_esperado>
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_entity import Bot
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.services.execution.protect_positions_service import (
    ProtectPositionsService,
)


# ======================================================================
# Helpers
# ======================================================================

def _make_bot(status: str = "paused") -> Bot:
    return Bot(
        id=1,
        name="Agente de prueba",
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=2,
        feature_set_id=1,
        mode="paper",
        status=status,
        risk_params={"risk_pct": 0.01},
    )


def _make_position(sl_order_id: int | None = None) -> Position:
    return Position(
        id=40,
        bot_id=1,
        symbol_id=5,
        qty=Decimal("2"),
        avg_price=Decimal("100"),
        stop_loss=Decimal("90"),
        take_profit=Decimal("130"),
        signal_id=11,
        sl_order_id=sl_order_id,
    )


def _make_service(
    positions: list[Position],
    low: str = "95",
    high: str = "110",
    bot: Bot | None = None,
    order_result: ServiceResult | None = None,
    candles: list | None = None,
):
    position_repo = MagicMock()
    position_repo.list_protected.return_value = positions

    bot_repo = MagicMock()
    bot_repo.get_by_id.return_value = bot if bot is not None else _make_bot()

    candle_repo = MagicMock()
    candle_repo.list_candles.return_value = (
        candles if candles is not None else [MagicMock(low=float(low), high=float(high))]
    )

    create_order = MagicMock()
    create_order.create.return_value = order_result or ServiceResult.ok(data=MagicMock(id=900))

    service = ProtectPositionsService(
        position_repo=position_repo,
        bot_repo=bot_repo,
        candle_repo=candle_repo,
        create_order=create_order,
    )
    return service, create_order, candle_repo


# ======================================================================
# TestStopLossAndTakeProfit
# ======================================================================

class TestStopLossAndTakeProfit:
    def test_candle_touching_stop_loss_sells_with_reason_stop_loss(self):
        service, create_order, _ = _make_service([_make_position()], low="89", high="100")

        result = service.run()

        assert result.success is True
        create_order.create.assert_called_once_with(
            bot_id=1,
            side="sell",
            order_type="market",
            qty=Decimal("2"),
            owner_id=None,
            require_running=False,
            reason="stop_loss",
        )
        assert result.data.closed == [
            {"bot_id": 1, "position_id": 40, "reason": "stop_loss", "order_id": 900}
        ]

    def test_candle_touching_take_profit_sells_with_reason_take_profit(self):
        service, create_order, _ = _make_service([_make_position()], low="120", high="131")

        result = service.run()

        kwargs = create_order.create.call_args.kwargs
        assert kwargs["reason"] == "take_profit"
        assert kwargs["require_running"] is False
        assert result.data.closed[0]["reason"] == "take_profit"

    def test_candle_touching_both_levels_stop_loss_wins(self):
        service, create_order, _ = _make_service([_make_position()], low="85", high="140")

        result = service.run()

        assert create_order.create.call_args.kwargs["reason"] == "stop_loss"
        assert result.data.closed[0]["reason"] == "stop_loss"

    def test_untouched_levels_do_nothing(self):
        service, create_order, _ = _make_service([_make_position()], low="95", high="120")

        result = service.run()

        create_order.create.assert_not_called()
        assert result.data.checked == 1
        assert result.data.closed == []
        assert result.data.failed == []

    def test_stopped_bot_is_still_protected(self):
        service, create_order, _ = _make_service(
            [_make_position()], low="89", high="100", bot=_make_bot(status="stopped")
        )

        service.run()

        create_order.create.assert_called_once()

    def test_uses_latest_candle_of_bot_timeframe(self):
        service, _, candle_repo = _make_service([_make_position()])

        service.run()

        candle_repo.list_candles.assert_called_once_with(symbol_id=5, timeframe_id=3, limit=1)


# ======================================================================
# TestNativeStop
# ======================================================================

class TestNativeStop:
    def test_stop_loss_touched_with_native_stop_does_nothing(self):
        service, create_order, _ = _make_service(
            [_make_position(sl_order_id=77)], low="85", high="100"
        )

        result = service.run()

        create_order.create.assert_not_called()
        assert result.data.closed == []
        assert result.data.failed == []

    def test_take_profit_touched_with_native_stop_sells(self):
        service, create_order, _ = _make_service(
            [_make_position(sl_order_id=77)], low="120", high="135"
        )

        result = service.run()

        assert create_order.create.call_args.kwargs["reason"] == "take_profit"
        assert result.data.closed[0]["order_id"] == 900


# ======================================================================
# TestFailuresAndSkips
# ======================================================================

class TestFailuresAndSkips:
    def test_create_order_failure_is_counted_as_failed(self):
        service, _, _ = _make_service(
            [_make_position(sl_order_id=77)],
            low="120",
            high="135",
            order_result=ServiceResult.fail(code="ORDER_NATIVE_STOP_ACTIVE", http_status=409),
        )

        result = service.run()

        assert result.success is True
        assert result.data.closed == []
        assert result.data.failed == [
            {
                "bot_id": 1,
                "position_id": 40,
                "reason": "take_profit",
                "code": "ORDER_NATIVE_STOP_ACTIVE",
            }
        ]

    def test_missing_bot_is_skipped(self):
        service, create_order, _ = _make_service([_make_position()], low="85")
        service._bot_repo.get_by_id.return_value = None

        result = service.run()

        create_order.create.assert_not_called()
        assert result.data.checked == 1

    def test_without_candles_is_skipped(self):
        service, create_order, _ = _make_service([_make_position()], candles=[])

        result = service.run()

        create_order.create.assert_not_called()
        assert result.data.checked == 1

    def test_one_failure_does_not_stop_other_positions(self):
        first, second = _make_position(), _make_position()
        second.id = 41
        service, create_order, _ = _make_service([first, second], low="85", high="100")
        create_order.create.side_effect = [
            ServiceResult.fail(code="RISK_KILL_SWITCH", http_status=409),
            ServiceResult.ok(data=MagicMock(id=901)),
        ]

        result = service.run()

        assert result.data.checked == 2
        assert [f["position_id"] for f in result.data.failed] == [40]
        assert [c["position_id"] for c in result.data.closed] == [41]
