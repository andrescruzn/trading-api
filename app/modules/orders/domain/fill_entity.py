# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/domain/fill_entity.py
#
# Entidad de dominio: Fill.
# Representa la ejecución (parcial o total) de una orden.
# Un fill es el registro inmutable de que dinero realmente se movió:
# precio de ejecución real, cantidad ejecutada y comisión cobrada.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal


class Fill:
    """
    Entidad de dominio: Fill.

    Un fill es generado cuando una orden se ejecuta en el exchange.
    Una misma orden puede tener múltiples fills si se ejecuta parcialmente
    (ej: se compran 0.3 BTC en una transacción y 0.7 BTC en otra).

    Campos clave:
    - qty   : cantidad ejecutada en este fill (> 0, siempre positivo)
    - price : precio al que se ejecutó este fill (precio real del exchange,
              o precio simulado en modo paper)
    - fee   : comisión cobrada por el exchange (0 en modo paper)
    - fee_asset : activo en el que se cobró la comisión (ej: "BNB", "USDT")
    """

    def __init__(
        self,
        id: int,
        order_id: int,
        qty: Decimal,
        price: Decimal,
        fee: Decimal = Decimal("0"),
        fee_asset: str | None = None,
        exchange_trade_id: str | None = None,
        ts: datetime | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.order_id = order_id
        self.exchange_trade_id = exchange_trade_id
        self.qty = qty
        self.price = price
        self.fee = fee
        self.fee_asset = fee_asset
        self.ts = ts
        self.created_at = created_at

    # ------------------------------------------------------------------
    # Cálculos financieros
    # ------------------------------------------------------------------

    def notional_value(self) -> Decimal:
        """
        Valor nocional del fill = precio × cantidad.
        Representa el monto total de activo base que se movió.
        Ej: 0.5 BTC a $60,000 = $30,000 de valor nocional.
        """
        return self.price * self.qty

    def is_valid(self) -> bool:
        """Un fill es válido si tiene cantidad y precio positivos."""
        return self.qty > Decimal("0") and self.price >= Decimal("0")
