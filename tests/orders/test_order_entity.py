# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_order_entity.py
#
# Tests unitarios de la entidad Order (M8).
#
# CUBRE:
# - Máquina de estados: can_transition_to / is_final.
# - build_client_order_id (idempotencia con el exchange).
# - requires_price / requires_stop_price por tipo de orden.
# - Validaciones de lado, tipo y estado.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.orders.domain.order_entity import Order


# ======================================================================
# Helpers
# ======================================================================

def _make_order(status: str = "new", type: str = "market", side: str = "buy") -> Order:
    return Order(
        id=1,
        bot_id=10,
        side=side,
        type=type,
        qty=Decimal("0.5"),
        status=status,
        meta={"symbol": "BTC/USDT", "mode": "paper"},
    )


# ======================================================================
# TestStateMachine
# ======================================================================

class TestStateMachine:

    @pytest.mark.parametrize(
        "current, target",
        [
            ("new", "sent"),
            ("new", "canceled"),
            # Se guarda `new` antes de enviarla y pasa directo al estado real
            ("new", "filled"),
            ("new", "partially_filled"),
            ("new", "rejected"),
            ("sent", "partially_filled"),
            ("sent", "filled"),
            ("sent", "canceled"),
            ("sent", "rejected"),
            ("partially_filled", "filled"),
            ("partially_filled", "canceled"),
        ],
    )
    def test_allowed_transitions_return_true(self, current, target):
        order = _make_order(status=current)

        assert order.can_transition_to(target) is True

    @pytest.mark.parametrize(
        "current, target",
        [
            # No se puede retroceder
            ("sent", "new"),
            ("partially_filled", "sent"),
            ("partially_filled", "rejected"),
        ],
    )
    def test_disallowed_transitions_return_false(self, current, target):
        order = _make_order(status=current)

        assert order.can_transition_to(target) is False

    @pytest.mark.parametrize("final_status", ["filled", "canceled", "rejected"])
    @pytest.mark.parametrize(
        "target",
        ["new", "sent", "partially_filled", "filled", "canceled", "rejected"],
    )
    def test_final_states_have_no_transitions(self, final_status, target):
        order = _make_order(status=final_status)

        assert order.can_transition_to(target) is False

    @pytest.mark.parametrize("status", list(Order.VALID_STATUSES))
    def test_same_status_is_not_a_transition(self, status):
        order = _make_order(status=status)

        assert order.can_transition_to(status) is False

    def test_unknown_current_status_cannot_transition(self):
        order = _make_order(status="flying")

        assert order.can_transition_to("sent") is False

    def test_unknown_target_status_is_rejected(self):
        order = _make_order(status="sent")

        assert order.can_transition_to("expired") is False


# ======================================================================
# TestIsFinal
# ======================================================================

class TestIsFinal:

    @pytest.mark.parametrize("status", ["filled", "canceled", "rejected"])
    def test_final_statuses(self, status):
        assert _make_order(status=status).is_final() is True

    @pytest.mark.parametrize("status", ["new", "sent", "partially_filled"])
    def test_open_statuses_are_not_final(self, status):
        assert _make_order(status=status).is_final() is False


# ======================================================================
# TestBuildClientOrderId
# ======================================================================

class TestBuildClientOrderId:

    def test_is_deterministic_from_internal_id(self):
        assert Order.build_client_order_id(42) == "ta-42"
        assert Order.build_client_order_id(42) == Order.build_client_order_id(42)

    def test_different_ids_produce_different_client_ids(self):
        assert Order.build_client_order_id(1) != Order.build_client_order_id(2)

    def test_fits_exchange_limit_for_large_bigint(self):
        # Binance/Bybit/OKX aceptan hasta 36 caracteres
        cid = Order.build_client_order_id(9_223_372_036_854_775_807)

        assert len(cid) <= 36
        assert cid.startswith("ta-")


# ======================================================================
# TestPriceRequirements
# ======================================================================

class TestPriceRequirements:

    @pytest.mark.parametrize(
        "order_type, needs_price, needs_stop",
        [
            ("market", False, False),
            ("limit", True, False),
            ("stop", False, True),
            ("stop_limit", True, True),
        ],
    )
    def test_requirements_by_type(self, order_type, needs_price, needs_stop):
        order = _make_order(type=order_type)

        assert order.requires_price() is needs_price
        assert order.requires_stop_price() is needs_stop


# ======================================================================
# TestBasicValidations
# ======================================================================

class TestBasicValidations:

    def test_valid_side_type_and_status(self):
        order = _make_order(status="new", type="limit", side="sell")

        assert order.is_valid_side() is True
        assert order.is_valid_type() is True
        assert order.is_valid_status() is True

    def test_invalid_side_type_and_status(self):
        order = _make_order(status="lost", type="iceberg", side="short")

        assert order.is_valid_side() is False
        assert order.is_valid_type() is False
        assert order.is_valid_status() is False

    def test_meta_defaults_to_empty_dict(self):
        order = Order(id=1, bot_id=1, side="buy", type="market", qty=Decimal("1"))

        assert order.meta == {}
        assert order.status == "new"
