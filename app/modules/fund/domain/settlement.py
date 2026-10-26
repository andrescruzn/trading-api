# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/settlement.py
#
# Cálculos puros de la liquidación de un agente (F4 + F5). Sin repositorios:
# la vista previa y la liquidación real usan exactamente las mismas cuentas.
#
# FLUJO DE CAJA (lo que operó el agente desde la última liquidación):
#   ventas (qty × precio) − compras (qty × precio) − comisiones en la moneda
#   del fondo (USDT). Con el agente sin posiciones, ese flujo es su resultado
#   exacto: equity nueva = equity anterior + flujo.
#
# COMISIONES DEL EXCHANGE EN OTRA MONEDA:
# - En la moneda base del par (p. ej. BTC en una compra): ya se reflejan en
#   lo que se vende después (se vende menos), no se restan dos veces.
# - En una tercera moneda (p. ej. BNB): no se valoran aquí; se informan en
#   `unvalued_fees` (recomendación: pagar las comisiones en USDT).
#
# ORDEN DE UNA LIQUIDACIÓN (todo al mismo NAV):
#   1. NAV = (equity anterior + flujo) / unidades.
#   2. Salidas (F5): por cada solicitud, lotes FIFO que cumplan la permanencia;
#      comisión escalonada sobre la ganancia y reparto entre propietarios.
#   3. Entradas (F4): cada asignación compra unidades al NAV.
# ======================================================================

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_DOWN, Decimal

from app.modules.fund.domain.agent_pool_entity import (
    PRECISION,
    AgentPool,
    AllocationOrder,
    RedemptionRequest,
    UnitLot,
)
from app.modules.fund.domain.commission import (
    CommissionShare,
    FeeTier,
    TierCharge,
    split_commission,
    tiered_fee,
)
from app.modules.orders.domain.fill_entity import BotFill

_ZERO = Decimal("0")


# ======================================================================
# Flujo de caja
# ======================================================================

@dataclass(frozen=True)
class CashFlow:
    sells: Decimal
    buys: Decimal
    fees: Decimal
    unvalued_fees: dict[str, Decimal]
    last_fill_id: int
    fills_count: int
    # Perpetuos en live: funding cobrado (+) o pagado (−) desde la última
    # liquidación, y el último registro contabilizado
    funding: Decimal = _ZERO
    last_funding_id: int = 0

    @property
    def net(self) -> Decimal:
        return self.sells - self.buys - self.fees + self.funding


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


# ======================================================================
# Plan de liquidación
# ======================================================================

@dataclass(frozen=True)
class PlannedAllocation:
    order: AllocationOrder
    units: Decimal


@dataclass(frozen=True)
class CanceledAllocation:
    order: AllocationOrder
    reason: str


@dataclass(frozen=True)
class PlannedRedemption:
    order: RedemptionRequest
    # (id del lote, unidades que salen de él)
    consumed: list[tuple[int, Decimal]]
    units: Decimal
    value: Decimal
    cost: Decimal
    fee: Decimal
    breakdown: list[TierCharge]
    commissions: list[tuple[int, Decimal]]
    # Lo pedido que no salió por la permanencia (None = salió todo lo pedido)
    pending_amount: Decimal | None

    @property
    def gain(self) -> Decimal:
        return self.value - self.cost

    @property
    def return_pct(self) -> Decimal:
        return (self.gain / self.cost).quantize(PRECISION) if self.cost > 0 else _ZERO

    @property
    def net(self) -> Decimal:
        return self.value - self.fee


@dataclass(frozen=True)
class SettlementPlan:
    previous_equity: Decimal
    trading_result: Decimal
    equity_before: Decimal
    units_before: Decimal
    nav: Decimal
    allocations: list[PlannedAllocation] = field(default_factory=list)
    canceled: list[CanceledAllocation] = field(default_factory=list)
    redemptions: list[PlannedRedemption] = field(default_factory=list)
    # Salidas sin nada que cumpla la permanencia: siguen en cola
    waiting_redemptions: list[RedemptionRequest] = field(default_factory=list)

    @property
    def allocated_amount(self) -> Decimal:
        return sum((a.order.amount for a in self.allocations), _ZERO)

    @property
    def units_issued(self) -> Decimal:
        return sum((a.units for a in self.allocations), _ZERO)

    @property
    def redeemed_amount(self) -> Decimal:
        return sum((r.value for r in self.redemptions), _ZERO)

    @property
    def units_redeemed(self) -> Decimal:
        return sum((r.units for r in self.redemptions), _ZERO)

    @property
    def fees_total(self) -> Decimal:
        return sum((r.fee for r in self.redemptions), _ZERO)

    @property
    def equity_after(self) -> Decimal:
        return self.equity_before - self.redeemed_amount + self.allocated_amount

    @property
    def units_after(self) -> Decimal:
        return self.units_before - self.units_redeemed + self.units_issued


def _plan_redemption(
    order: RedemptionRequest,
    lots: list[UnitLot],
    remaining: dict[int, Decimal],
    *,
    nav: Decimal,
    hold_cutoff: datetime | None,
    fee_tiers: list[FeeTier],
    shares: list[CommissionShare],
) -> PlannedRedemption | None:
    """Lotes FIFO de la persona que cumplen la permanencia; None si no hay ninguno."""
    eligible = [
        lot
        for lot in lots
        if lot.user_id == order.user_id
        and remaining.get(lot.id, _ZERO) > 0
        and (hold_cutoff is None or (lot.acquired_at is not None and lot.acquired_at <= hold_cutoff))
    ]
    eligible_units = sum((remaining[lot.id] for lot in eligible), _ZERO)
    if eligible_units <= 0 or nav <= 0:
        return None

    wanted = (
        eligible_units
        if order.amount is None
        else min(eligible_units, (order.amount / nav).quantize(PRECISION, rounding=ROUND_DOWN))
    )
    if wanted <= 0:
        return None

    consumed: list[tuple[int, Decimal]] = []
    cost = _ZERO
    left = wanted
    for lot in eligible:
        if left <= 0:
            break
        take = min(left, remaining[lot.id])
        consumed.append((lot.id, take))
        cost += (lot.cost * take / lot.units).quantize(PRECISION)
        remaining[lot.id] -= take
        left -= take

    value = (wanted * nav).quantize(PRECISION, rounding=ROUND_DOWN)
    fee, breakdown = tiered_fee(cost, value - cost, fee_tiers)
    pending = None
    if order.amount is not None and value < order.amount:
        pending = (order.amount - value).quantize(PRECISION)
    return PlannedRedemption(
        order=order,
        consumed=consumed,
        units=wanted,
        value=value,
        cost=cost,
        fee=fee,
        breakdown=breakdown,
        commissions=split_commission(fee, shares),
        pending_amount=pending,
    )


def plan_settlement(
    pool: AgentPool,
    flow: CashFlow,
    queued: list[AllocationOrder],
    available_balance: dict[tuple[int, str], Decimal],
    *,
    redemptions: list[RedemptionRequest] | None = None,
    lots: list[UnitLot] | None = None,
    hold_cutoff: datetime | None = None,
    fee_tiers: list[FeeTier] | None = None,
    shares: list[CommissionShare] | None = None,
) -> SettlementPlan:
    """
    Calcula la liquidación sin escribir nada.

    - equity_before = equity anterior + flujo neto; NAV = equity_before / unidades
      (1 si aún no hay unidades).
    - Salidas: lotes de la persona con `acquired_at <= hold_cutoff`, del más
      viejo al más nuevo; comisión escalonada sobre la ganancia y su reparto.
      Si no hay nada que cumpla la permanencia, la solicitud sigue en cola.
    - Entradas: cada asignación compra unidades al NAV si la persona todavía
      tiene ese saldo (`available_balance[(user, bucket)]`); si no, se cancela.
    """
    equity_before = pool.equity + flow.net
    nav = (
        (equity_before / pool.units).quantize(PRECISION)
        if pool.units > 0
        else Decimal("1")
    )

    # 1. Salidas
    live_lots = sorted(lots or [], key=lambda lot: (lot.acquired_at or datetime.min, lot.id))
    remaining = {lot.id: lot.units_remaining for lot in live_lots}
    planned_out: list[PlannedRedemption] = []
    waiting: list[RedemptionRequest] = []
    for order in sorted(redemptions or [], key=lambda o: o.id):
        planned = _plan_redemption(
            order,
            live_lots,
            remaining,
            nav=nav,
            hold_cutoff=hold_cutoff,
            fee_tiers=fee_tiers or [],
            shares=shares or [],
        )
        if planned is None:
            waiting.append(order)
        else:
            planned_out.append(planned)

    # Si salen todas las unidades y no entra nadie, la última salida se lleva
    # el residuo del redondeo: un agente sin unidades no puede quedar con saldo.
    redeemed_units = sum((r.units for r in planned_out), _ZERO)
    if planned_out and pool.units - redeemed_units == 0 and not queued:
        residual = equity_before - sum((r.value for r in planned_out), _ZERO)
        if residual != 0:
            last = planned_out[-1]
            planned_out[-1] = PlannedRedemption(
                order=last.order,
                consumed=last.consumed,
                units=last.units,
                value=last.value + residual,
                cost=last.cost,
                fee=last.fee,
                breakdown=last.breakdown,
                commissions=last.commissions,
                pending_amount=last.pending_amount,
            )

    # 2. Entradas
    available = dict(available_balance)
    planned_in: list[PlannedAllocation] = []
    canceled: list[CanceledAllocation] = []
    for order in sorted(queued, key=lambda o: o.id):
        key = (order.user_id, order.source_bucket)
        if available.get(key, _ZERO) < order.amount:
            canceled.append(CanceledAllocation(order, "insufficient_balance"))
            continue
        if nav <= 0:
            canceled.append(CanceledAllocation(order, "invalid_nav"))
            continue
        available[key] = available.get(key, _ZERO) - order.amount
        units = (order.amount / nav).quantize(PRECISION, rounding=ROUND_DOWN)
        planned_in.append(PlannedAllocation(order, units))

    return SettlementPlan(
        previous_equity=pool.equity,
        trading_result=flow.net,
        equity_before=equity_before,
        units_before=pool.units,
        nav=nav,
        allocations=planned_in,
        canceled=canceled,
        redemptions=planned_out,
        waiting_redemptions=waiting,
    )
