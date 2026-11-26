# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/orders/position_updater.py
#
# Aplica una ejecución (fill) a la posición del bot en su símbolo. Lo usan
# CreateOrderService (ejecución inmediata) y ReconcileOrdersService (lo
# que el exchange ejecutó después).
#
# - Sin posición: la crea con qty y avg_price del fill.
# - Con posición: apply_buy_fill / apply_sell_fill recalculan el precio
#   promedio ponderado (WAP) y el P&L realizado (lógica pura de Position).
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from app.modules.bots.domain.bot_entity import Bot
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.domain.position_repository import PositionRepository


def apply_fill(
    position_repo: PositionRepository,
    bot: Bot,
    position: Position | None,
    fill_qty: Decimal,
    fill_price: Decimal,
    side: str,
) -> Position:
    """Crea o actualiza la posición (sin commit: lo hace el servicio)."""
    is_new = position is None
    if position is None:
        # Primera operación del bot en este símbolo — crear posición nueva
        position = Position(
            id=0,
            bot_id=bot.id,
            symbol_id=bot.symbol_id,
            qty=Decimal("0"),
            avg_price=Decimal("0"),
            realized_pnl=Decimal("0"),
        )

    if side == "buy":
        position.apply_buy_fill(fill_qty, fill_price)
    else:
        position.apply_sell_fill(fill_qty, fill_price)

    if is_new:
        return position_repo.create(position)
    return position_repo.update(position)
