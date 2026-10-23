# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/settlement.py
#
# Cálculos puros de la liquidación de un agente (F4). Sin repositorios:
# la vista previa y la liquidación real usan exactamente las mismas cuentas.
#
# FLUJO DE CAJA (lo que operó el agente desde la última liquidación):
#   ventas (qty × precio) − compras (qty × precio) − comisiones en la moneda
#   del fondo (USDT). Con el agente sin posiciones, ese flujo es su resultado
#   exacto: equity nueva = equity anterior + flujo.
#
# COMISIONES EN OTRA MONEDA:
# - En la moneda base del par (p. ej. BTC en una compra): ya se reflejan en
#   lo que se vende después (se vende menos), no se restan dos veces.
# - En una tercera moneda (p. ej. BNB): no se valoran aquí; se informan en
#   `unvalued_fees` para que los propietarios las vean (recomendación:
#   desactivar el pago de comisiones con BNB en la billetera).
# ======================================================================

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal

from app.modules.fund.domain.agent_pool_entity import PRECISION, AgentPool, AllocationOrder
from app.modules.orders.domain.fill_entity import BotFill

_ZERO = Decimal("0")


@dataclass(frozen=True)
class CashFlow:
    sells: Decimal
    buys: Decimal
    fees: Decimal
    unvalued_fees: dict[str, Decimal]
    last_fill_id: int
    fills_count: int

    @property
    def net(self) -> Decimal:
        return self.sells - self.buys - self.fees


def cash_flow(
    fills: list[BotFill], *, quote: str, base: str | None, after_fill_id: int
) -> CashFlow:
    """Flujo de caja de los fills (en `quote`) y el último fill contabilizado."""
    quote = quote.upper()
    base = (base or "").upper()
    sells = buys = fees = _ZERO
    unvalued: dict[str, Decimal] = defaultdict(lambda: _ZERO)
    last_id = after_fill_id
    for fill in fills:
        notional = fill.qty * fill.price
        if fill.side == "sell":
            sells += notional
        else:
            buys += notional
        fee_asset = (fill.fee_asset or quote).upper()
        if fill.fee:
            if fee_asset == quote:
                fees += fill.fee
            elif fee_asset != base:
                unvalued[fee_asset] += fill.fee
        last_id = max(last_id, fill.id)
    return CashFlow(sells, buys, fees, dict(unvalued), last_id, len(fills))


@dataclass(frozen=True)
class PlannedAllocation:
    order: AllocationOrder
    units: Decimal


@dataclass(frozen=True)
class CanceledAllocation:
    order: AllocationOrder
    reason: str


@dataclass(frozen=True)
class SettlementPlan:
    previous_equity: Decimal
    trading_result: Decimal
    equity_before: Decimal
    units_before: Decimal
    nav: Decimal
    allocations: list[PlannedAllocation] = field(default_factory=list)
    canceled: list[CanceledAllocation] = field(default_factory=list)

    @property
    def allocated_amount(self) -> Decimal:
        return sum((a.order.amount for a in self.allocations), _ZERO)

    @property
    def units_issued(self) -> Decimal:
        return sum((a.units for a in self.allocations), _ZERO)

    @property
    def equity_after(self) -> Decimal:
        return self.equity_before + self.allocated_amount

    @property
    def units_after(self) -> Decimal:
        return self.units_before + self.units_issued


def plan_settlement(
    pool: AgentPool,
    flow: CashFlow,
    queued: list[AllocationOrder],
    available_balance: dict[tuple[int, str], Decimal],
) -> SettlementPlan:
    """
    Calcula la liquidación sin escribir nada.

    - equity_before = equity anterior + flujo neto; NAV = equity_before / unidades
      (1 si aún no hay unidades).
    - Cada asignación en cola compra unidades al NAV, si la persona todavía
      tiene ese saldo en el bucket de origen (`available_balance[(user, bucket)]`,
      que se va descontando); si no, se cancela con motivo.
    """
    equity_before = pool.equity + flow.net
    nav = (
        (equity_before / pool.units).quantize(PRECISION)
        if pool.units > 0
        else Decimal("1")
    )
    remaining = dict(available_balance)
    planned: list[PlannedAllocation] = []
    canceled: list[CanceledAllocation] = []
    for order in sorted(queued, key=lambda o: o.id):
        key = (order.user_id, order.source_bucket)
        if remaining.get(key, _ZERO) < order.amount:
            canceled.append(CanceledAllocation(order, "insufficient_balance"))
            continue
        if nav <= 0:
            canceled.append(CanceledAllocation(order, "invalid_nav"))
            continue
        remaining[key] = remaining.get(key, _ZERO) - order.amount
        units = (order.amount / nav).quantize(PRECISION, rounding=ROUND_DOWN)
        planned.append(PlannedAllocation(order, units))
    return SettlementPlan(
        previous_equity=pool.equity,
        trading_result=flow.net,
        equity_before=equity_before,
        units_before=pool.units,
        nav=nav,
        allocations=planned,
        canceled=canceled,
    )
