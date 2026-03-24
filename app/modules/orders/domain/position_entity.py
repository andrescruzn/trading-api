# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/domain/position_entity.py
#
# Entidad de dominio: Position.
# Representa la posición abierta actual de un bot en un símbolo.
# Registra la cantidad acumulada, el precio promedio de entrada
# (weighted average price) y el P&L realizado acumulado.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal


class Position:
    """
    Entidad de dominio: Position.

    Una posición es el resultado acumulado de todas las órdenes ejecutadas
    por un bot sobre un símbolo específico.

    Campos clave:
    - qty         : cantidad de activo base actualmente en posición (≥ 0)
    - avg_price   : precio promedio de entrada ponderado por cantidad
    - realized_pnl: ganancia/pérdida acumulada de operaciones ya cerradas

    Reglas de negocio:
    - qty = 0 significa posición cerrada (flat)
    - avg_price se recalcula en cada compra mediante weighted average
    - realized_pnl se acumula cada vez que se vende parte de la posición
    """

    def __init__(
        self,
        id: int,
        bot_id: int,
        symbol_id: int,
        qty: Decimal = Decimal("0"),
        avg_price: Decimal = Decimal("0"),
        realized_pnl: Decimal = Decimal("0"),
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.bot_id = bot_id
        self.symbol_id = symbol_id
        self.qty = qty
        self.avg_price = avg_price
        self.realized_pnl = realized_pnl
        self.updated_at = updated_at

    # ------------------------------------------------------------------
    # Cálculos financieros
    # ------------------------------------------------------------------

    def unrealized_pnl(self, current_price: Decimal) -> Decimal:
        """
        P&L no realizado = (precio_actual - avg_price) × qty.

        Representa cuánto ganaríamos/perderíamos si cerráramos
        la posición ahora mismo al precio actual del mercado.

        Retorna Decimal("0") si la posición está cerrada (qty = 0).
        """
        if self.qty == Decimal("0"):
            return Decimal("0")
        return (current_price - self.avg_price) * self.qty

    def apply_buy_fill(self, fill_qty: Decimal, fill_price: Decimal) -> None:
        """
        Actualiza la posición al recibir una compra ejecutada.

        Recalcula el precio promedio ponderado (WAP):
          nuevo_avg = (qty_actual × avg_price + fill_qty × fill_price)
                      / (qty_actual + fill_qty)

        Ejemplo:
          Posición: 0.5 BTC @ $60,000
          Compra:   0.5 BTC @ $62,000
          Resultado: 1.0 BTC @ $61,000 (promedio ponderado)
        """
        total_qty = self.qty + fill_qty
        if total_qty == Decimal("0"):
            return

        self.avg_price = (
            (self.qty * self.avg_price + fill_qty * fill_price) / total_qty
        )
        self.qty = total_qty

    def apply_sell_fill(self, fill_qty: Decimal, fill_price: Decimal) -> None:
        """
        Actualiza la posición al recibir una venta ejecutada.

        Reduce la cantidad y acumula el P&L realizado:
          pnl_realizado = (precio_venta - avg_price) × qty_vendida

        Si se vende toda la posición, avg_price se resetea a 0.
        """
        pnl = (fill_price - self.avg_price) * fill_qty
        self.realized_pnl += pnl
        self.qty -= fill_qty

        # Si la posición queda flat, resetear el precio promedio
        if self.qty <= Decimal("0"):
            self.qty = Decimal("0")
            self.avg_price = Decimal("0")

    def is_flat(self) -> bool:
        """Retorna True si la posición está cerrada (sin activo en cartera)."""
        return self.qty == Decimal("0")
