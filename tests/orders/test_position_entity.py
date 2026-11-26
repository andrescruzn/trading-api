# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_position_entity.py
#
# Tests unitarios de la entidad Position (M8).
#
# CUBRE:
# - WAP en apply_buy_fill y P&L realizado en apply_sell_fill.
# - Protección (SL/TP) borrada al quedar flat.
# - set_protection / clear_protection / has_native_stop.
# - protection_hit (SL gana si la vela toca los dos niveles).
# - is_flat / unrealized_pnl.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from app.modules.orders.domain.position_entity import Position


# ======================================================================
# Helpers
# ======================================================================

def _make_position(
    qty: str = "0",
    avg_price: str = "0",
    realized_pnl: str = "0",
    stop_loss: str | None = None,
    take_profit: str | None = None,
    signal_id: int | None = None,
    sl_order_id: int | None = None,
) -> Position:
    return Position(
        id=1,
        bot_id=10,
        symbol_id=5,
        qty=Decimal(qty),
        avg_price=Decimal(avg_price),
        realized_pnl=Decimal(realized_pnl),
        stop_loss=Decimal(stop_loss) if stop_loss is not None else None,
        take_profit=Decimal(take_profit) if take_profit is not None else None,
        signal_id=signal_id,
        sl_order_id=sl_order_id,
    )


# ======================================================================
# TestApplyBuyFill
# ======================================================================

class TestApplyBuyFill:

    def test_first_buy_sets_qty_and_avg_price(self):
        pos = _make_position()

        pos.apply_buy_fill(Decimal("1"), Decimal("100"))

        assert pos.qty == Decimal("1")
        assert pos.avg_price == Decimal("100")

    def test_second_buy_recalculates_weighted_average(self):
        pos = _make_position()

        pos.apply_buy_fill(Decimal("1"), Decimal("100"))
        pos.apply_buy_fill(Decimal("1"), Decimal("200"))

        assert pos.qty == Decimal("2")
        assert pos.avg_price == Decimal("150")

    def test_weighted_average_uses_quantities(self):
        # 0.5 @ 60 000 + 1.5 @ 62 000 → 2 @ 61 500
        pos = _make_position(qty="0.5", avg_price="60000")

        pos.apply_buy_fill(Decimal("1.5"), Decimal("62000"))

        assert pos.qty == Decimal("2.0")
        assert pos.avg_price == Decimal("61500")

    def test_buy_does_not_touch_realized_pnl(self):
        pos = _make_position(realized_pnl="25")

        pos.apply_buy_fill(Decimal("1"), Decimal("100"))

        assert pos.realized_pnl == Decimal("25")

    def test_zero_fill_on_flat_position_is_noop(self):
        pos = _make_position()

        pos.apply_buy_fill(Decimal("0"), Decimal("100"))

        assert pos.qty == Decimal("0")
        assert pos.avg_price == Decimal("0")


# ======================================================================
# TestApplySellFill
# ======================================================================

class TestApplySellFill:

    def test_partial_sell_realizes_pnl_and_keeps_avg_price(self):
        # buy 1 @ 100 + buy 1 @ 200 → avg 150; sell 1 @ 180 → +30
        pos = _make_position()
        pos.apply_buy_fill(Decimal("1"), Decimal("100"))
        pos.apply_buy_fill(Decimal("1"), Decimal("200"))

        pos.apply_sell_fill(Decimal("1"), Decimal("180"))

        assert pos.realized_pnl == Decimal("30")
        assert pos.qty == Decimal("1")
        assert pos.avg_price == Decimal("150")

    def test_losing_sell_accumulates_negative_pnl(self):
        pos = _make_position(qty="2", avg_price="150", realized_pnl="30")

        pos.apply_sell_fill(Decimal("1"), Decimal("120"))

        assert pos.realized_pnl == Decimal("0")  # 30 + (120 − 150) × 1

    def test_full_sell_leaves_position_flat_and_resets_avg_price(self):
        pos = _make_position(qty="2", avg_price="150")

        pos.apply_sell_fill(Decimal("2"), Decimal("160"))

        assert pos.qty == Decimal("0")
        assert pos.avg_price == Decimal("0")
        assert pos.realized_pnl == Decimal("20")
        assert pos.is_flat() is True

    def test_full_sell_clears_protection_and_native_stop(self):
        pos = _make_position(
            qty="1", avg_price="100",
            stop_loss="90", take_profit="120", signal_id=7, sl_order_id=55,
        )

        pos.apply_sell_fill(Decimal("1"), Decimal("120"))

        assert pos.stop_loss is None
        assert pos.take_profit is None
        assert pos.signal_id is None
        assert pos.sl_order_id is None

    def test_partial_sell_keeps_protection(self):
        pos = _make_position(
            qty="2", avg_price="100",
            stop_loss="90", take_profit="120", signal_id=7, sl_order_id=55,
        )

        pos.apply_sell_fill(Decimal("1"), Decimal("110"))

        assert pos.stop_loss == Decimal("90")
        assert pos.take_profit == Decimal("120")
        assert pos.signal_id == 7
        assert pos.sl_order_id == 55

    def test_oversell_clamps_qty_to_zero(self):
        # Spot sin cortos: qty nunca queda negativa
        pos = _make_position(qty="1", avg_price="100")

        pos.apply_sell_fill(Decimal("1.5"), Decimal("100"))

        assert pos.qty == Decimal("0")
        assert pos.avg_price == Decimal("0")

    def test_oversell_pnl_counts_only_held_qty(self):
        # Vender 1.5 cuando hay 1 @ 100, a 110: el P&L es sobre 1 → +10, no +15
        pos = _make_position(qty="1", avg_price="100")

        pos.apply_sell_fill(Decimal("1.5"), Decimal("110"))

        assert pos.realized_pnl == Decimal("10")

    def test_new_position_after_flat_does_not_inherit_avg_price(self):
        pos = _make_position(qty="1", avg_price="100")
        pos.apply_sell_fill(Decimal("1"), Decimal("110"))

        pos.apply_buy_fill(Decimal("1"), Decimal("200"))

        assert pos.avg_price == Decimal("200")
        assert pos.realized_pnl == Decimal("10")


# ======================================================================
# TestProtection
# ======================================================================

class TestProtection:

    def test_set_protection_stores_levels_and_signal(self):
        pos = _make_position(qty="1", avg_price="100")

        pos.set_protection(Decimal("95"), Decimal("110"), 3)

        assert pos.stop_loss == Decimal("95")
        assert pos.take_profit == Decimal("110")
        assert pos.signal_id == 3

    def test_set_protection_does_not_touch_native_stop(self):
        pos = _make_position(qty="1", avg_price="100", sl_order_id=55)

        pos.set_protection(Decimal("95"), Decimal("110"), 3)

        assert pos.sl_order_id == 55

    def test_clear_protection_also_clears_sl_order_id(self):
        pos = _make_position(
            qty="1", avg_price="100",
            stop_loss="90", take_profit="120", signal_id=7, sl_order_id=55,
        )

        pos.clear_protection()

        assert pos.stop_loss is None
        assert pos.take_profit is None
        assert pos.signal_id is None
        assert pos.sl_order_id is None
        assert pos.has_native_stop() is False

    def test_has_native_stop_true_with_sl_order_id(self):
        assert _make_position(sl_order_id=55).has_native_stop() is True

    def test_has_native_stop_false_without_sl_order_id(self):
        assert _make_position(stop_loss="90").has_native_stop() is False


# ======================================================================
# TestProtectionHit
# ======================================================================

class TestProtectionHit:

    def test_low_touching_stop_loss_returns_stop_loss(self):
        pos = _make_position(qty="1", avg_price="100", stop_loss="90", take_profit="120")

        assert pos.protection_hit(low=Decimal("90"), high=Decimal("101")) == "stop_loss"

    def test_high_touching_take_profit_returns_take_profit(self):
        pos = _make_position(qty="1", avg_price="100", stop_loss="90", take_profit="120")

        assert pos.protection_hit(low=Decimal("95"), high=Decimal("120")) == "take_profit"

    def test_stop_loss_wins_when_candle_touches_both(self):
        # Sin datos intravela se asume el peor caso
        pos = _make_position(qty="1", avg_price="100", stop_loss="90", take_profit="120")

        assert pos.protection_hit(low=Decimal("85"), high=Decimal("125")) == "stop_loss"

    def test_none_when_neither_level_touched(self):
        pos = _make_position(qty="1", avg_price="100", stop_loss="90", take_profit="120")

        assert pos.protection_hit(low=Decimal("90.01"), high=Decimal("119.99")) is None

    def test_none_when_position_is_flat(self):
        pos = _make_position(qty="0", stop_loss="90", take_profit="120")

        assert pos.protection_hit(low=Decimal("50"), high=Decimal("200")) is None

    def test_none_without_protection_levels(self):
        pos = _make_position(qty="1", avg_price="100")

        assert pos.protection_hit(low=Decimal("1"), high=Decimal("1000")) is None

    def test_only_take_profit_configured(self):
        pos = _make_position(qty="1", avg_price="100", take_profit="120")

        assert pos.protection_hit(low=Decimal("1"), high=Decimal("119")) is None
        assert pos.protection_hit(low=Decimal("1"), high=Decimal("121")) == "take_profit"


# ======================================================================
# TestFlatAndUnrealizedPnl
# ======================================================================

class TestFlatAndUnrealizedPnl:

    def test_is_flat_with_zero_qty(self):
        assert _make_position(qty="0").is_flat() is True

    def test_is_not_flat_with_qty(self):
        assert _make_position(qty="0.001").is_flat() is False

    def test_unrealized_pnl_gain(self):
        pos = _make_position(qty="2", avg_price="150")

        assert pos.unrealized_pnl(Decimal("180")) == Decimal("60")

    def test_unrealized_pnl_loss(self):
        pos = _make_position(qty="2", avg_price="150")

        assert pos.unrealized_pnl(Decimal("140")) == Decimal("-20")

    def test_unrealized_pnl_zero_when_flat(self):
        pos = _make_position(qty="0", avg_price="0")

        assert pos.unrealized_pnl(Decimal("180")) == Decimal("0")
