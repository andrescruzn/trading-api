# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/domain/order_entity.py
#
# Entidad de dominio: Order.
# Representa una orden de compra o venta emitida por un bot hacia
# un exchange. Una orden puede ejecutarse total o parcialmente
# (via fills) y tiene una máquina de estados bien definida.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any


class Order:
    """
    Entidad de dominio: Order.

    Una orden es la instrucción formal de comprar o vender un activo
    a un precio y cantidad determinados. Es creada por un bot a partir
    de una señal y ejecutada en el exchange (real o simulado).

    Lados válidos (side):
    - buy  : compra del activo base (ej: comprar BTC)
    - sell : venta del activo base (ej: vender BTC)

    Tipos válidos (type):
    - market     : ejecutar al precio actual del mercado
    - limit      : ejecutar solo si el precio llega a `price`
    - stop       : disparar una orden de mercado cuando el precio toca `stop_price`
    - stop_limit : disparar una orden límite cuando el precio toca `stop_price`

    Estados válidos y transiciones permitidas:
    - new              → sent, canceled
    - sent             → partially_filled, filled, canceled, rejected
    - partially_filled → filled, canceled
    - filled           → (estado final, sin transiciones)
    - canceled         → (estado final, sin transiciones)
    - rejected         → (estado final, sin transiciones)
    """

    VALID_SIDES = ("buy", "sell")
    VALID_TYPES = ("market", "limit", "stop", "stop_limit")
    VALID_STATUSES = (
        "new",
        "sent",
        "partially_filled",
        "filled",
        "canceled",
        "rejected",
    )

    # Mapa de transiciones válidas: estado_actual → estados_permitidos
    _ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
        "new":              ("sent", "canceled"),
        "sent":             ("partially_filled", "filled", "canceled", "rejected"),
        "partially_filled": ("filled", "canceled"),
        "filled":           (),
        "canceled":         (),
        "rejected":         (),
    }

    def __init__(
        self,
        id: int,
        bot_id: int,
        side: str,
        type: str,
        qty: Decimal,
        status: str = "new",
        signal_id: int | None = None,
        exchange_order_id: str | None = None,
        price: Decimal | None = None,
        stop_price: Decimal | None = None,
        time_in_force: str | None = None,
        meta: dict[str, Any] | None = None,
        ts: datetime | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.bot_id = bot_id
        self.signal_id = signal_id
        self.exchange_order_id = exchange_order_id
        self.side = side
        self.type = type
        self.status = status
        self.qty = qty
        self.price = price
        self.stop_price = stop_price
        self.time_in_force = time_in_force
        self.meta = meta or {}
        self.ts = ts
        self.created_at = created_at

    # ------------------------------------------------------------------
    # Validaciones de negocio
    # ------------------------------------------------------------------

    def is_valid_side(self) -> bool:
        return self.side in self.VALID_SIDES

    def is_valid_type(self) -> bool:
        return self.type in self.VALID_TYPES

    def is_valid_status(self) -> bool:
        return self.status in self.VALID_STATUSES

    def can_transition_to(self, new_status: str) -> bool:
        """
        Verifica si la transición de estado es válida.

        Ejemplo: una orden 'filled' no puede volver a 'new'.
        Esto protege la integridad del historial de órdenes.
        """
        if self.status == new_status:
            return False
        allowed = self._ALLOWED_TRANSITIONS.get(self.status, ())
        return new_status in allowed

    def is_final(self) -> bool:
        """
        Una orden está en estado final cuando ya no puede cambiar.
        Estados finales: filled, canceled, rejected.
        """
        return self.status in ("filled", "canceled", "rejected")

    def requires_price(self) -> bool:
        """
        Las órdenes limit requieren un precio límite.
        Las órdenes market NO usan precio (se ejecutan al precio actual).
        """
        return self.type in ("limit", "stop_limit")

    def requires_stop_price(self) -> bool:
        """
        Las órdenes stop y stop_limit requieren un precio de activación.
        """
        return self.type in ("stop", "stop_limit")
