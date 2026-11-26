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

    Protección (stop loss / take profit de la señal que la abrió):
    - Si la posición la abrió una señal aprobada, guarda su SL/TP y el
      scheduler la cierra a mercado cuando una vela los toca.
    - Al quedar flat se borra la protección.
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
        stop_loss: Decimal | None = None,
        take_profit: Decimal | None = None,
        signal_id: int | None = None,
        sl_order_id: int | None = None,
    ):
        self.id = id
        self.bot_id = bot_id
        self.symbol_id = symbol_id
        self.qty = qty
        self.avg_price = avg_price
        self.realized_pnl = realized_pnl
        self.updated_at = updated_at
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.signal_id = signal_id
        # Orden stop nativa en el exchange (live); None = la vigila el scheduler
        self.sl_order_id = sl_order_id

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

        Si se vende toda la posición, avg_price se resetea a 0. El P&L se
        calcula solo sobre lo que había (en spot no se vende de más).
        """
        sold_qty = min(fill_qty, self.qty)
        pnl = (fill_price - self.avg_price) * sold_qty
        self.realized_pnl += pnl
        self.qty -= fill_qty

        # Si la posición queda flat, resetear el precio promedio y la protección
        if self.qty <= Decimal("0"):
            self.qty = Decimal("0")
            self.avg_price = Decimal("0")
            self.clear_protection()

    def set_protection(
        self,
        stop_loss: Decimal | None,
        take_profit: Decimal | None,
        signal_id: int | None,
    ) -> None:
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.signal_id = signal_id

    def clear_protection(self) -> None:
        self.stop_loss = None
        self.take_profit = None
        self.signal_id = None
        self.sl_order_id = None

    def has_native_stop(self) -> bool:
        return self.sl_order_id is not None

    def protection_hit(self, low: Decimal, high: Decimal) -> str | None:
        """
        Qué nivel tocó la vela (solo largos): "stop_loss", "take_profit" o None.

        Si la misma vela toca los dos, gana el stop loss: sin datos intravela
        no se sabe cuál llegó primero y se asume el peor caso.
        """
        if self.is_flat():
            return None
        if self.stop_loss is not None and low <= self.stop_loss:
            return "stop_loss"
        if self.take_profit is not None and high >= self.take_profit:
            return "take_profit"
        return None

    def is_flat(self) -> bool:
        """Retorna True si la posición está cerrada (sin activo en cartera)."""
        return self.qty == Decimal("0")
