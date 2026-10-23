# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/agent_pool_entity.py
#
# Entidades del capital de los agentes en el fondo común (F4):
#
# - AgentPool       → el dinero de un agente: equity de la última
#                     liquidación (exacta) y unidades en circulación.
#                     NAV = equity / unidades (1 en la primera liquidación).
# - UnitLot         → unidades de una persona en un agente, compradas en una
#                     liquidación a un NAV; la fecha cuenta para la
#                     permanencia mínima (FIFO al redimir, F5).
# - AllocationOrder → "X USDT de esta persona a este agente": espera en cola
#                     a la próxima liquidación.
# - AgentSettlement → la liquidación: el momento exacto (agente pausado y sin
#                     posiciones) en que se calcula la equity y entran o
#                     salen participantes.
# - RedemptionRequest  → (F5) "saca X USDT (o todo) de este agente": espera a
#                        la próxima liquidación; sale solo lo que cumple la
#                        permanencia mínima.
# - SettlementRedemption → (F5) lo que salió en una liquidación, con la
#                        comisión tramo por tramo (lo ve la persona).
# - CommissionCredit   → (F5) la parte de una comisión que recibió un
#                        propietario.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

ALLOCATION_STATUSES = ("queued", "applied", "canceled")
REDEMPTION_STATUSES = ("queued", "applied", "canceled")
ALLOCATION_SOURCES = ("pending", "available")

# Unidades y NAV con la precisión de las columnas DECIMAL(30,12)
PRECISION = Decimal("0.000000000001")
INITIAL_NAV = Decimal("1")


@dataclass
class AgentPool:
    id: int
    bot_id: int
    asset: str
    equity: Decimal = Decimal("0")
    units: Decimal = Decimal("0")
    # Último fill del bot ya contabilizado: lo anterior (p. ej. pruebas antes
    # de abrir el agente al fondo) nunca entra en su equity.
    last_fill_id: int = 0
    last_settlement_id: int | None = None
    created_by_user_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Solo en memoria durante una liquidación: la liquidación que había al
    # leer el pool (para el UPDATE condicional)
    previous_settlement_id: int | None = None

    def apply_settlement(
        self, *, settlement_id: int, equity: Decimal, units: Decimal, last_fill_id: int
    ) -> None:
        self.previous_settlement_id = self.last_settlement_id
        self.last_settlement_id = settlement_id
        self.equity = equity
        self.units = units
        self.last_fill_id = last_fill_id

    @property
    def nav(self) -> Decimal:
        """Valor de una unidad en la última liquidación."""
        if self.units <= 0:
            return INITIAL_NAV
        return (self.equity / self.units).quantize(PRECISION)


@dataclass
class UnitLot:
    id: int
    pool_id: int
    user_id: int
    units: Decimal
    units_remaining: Decimal
    cost: Decimal
    nav_at_entry: Decimal
    settlement_id: int | None = None
    acquired_at: datetime | None = None

    @property
    def cost_remaining(self) -> Decimal:
        """Costo de las unidades que siguen vivas (proporcional)."""
        if self.units <= 0:
            return Decimal("0")
        return (self.cost * self.units_remaining / self.units).quantize(PRECISION)


@dataclass
class AllocationOrder:
    id: int
    pool_id: int
    user_id: int
    amount: Decimal
    source_bucket: str = "pending"
    status: str = "queued"
    note: str | None = None
    settlement_id: int | None = None
    created_by_user_id: int | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None


@dataclass
class AgentSettlement:
    id: int
    pool_id: int
    bot_id: int
    previous_equity: Decimal
    trading_result: Decimal
    equity_before: Decimal
    units_before: Decimal
    nav: Decimal
    allocated_amount: Decimal
    units_issued: Decimal
    equity_after: Decimal
    units_after: Decimal
    last_fill_id: int
    fills_count: int = 0
    unvalued_fees: dict[str, str] = field(default_factory=dict)
    note: str | None = None
    created_by_user_id: int | None = None
    settled_at: datetime | None = None
    # F5: lo que salió del agente en esta liquidación
    redeemed_amount: Decimal = Decimal("0")
    units_redeemed: Decimal = Decimal("0")
    fees_total: Decimal = Decimal("0")


@dataclass
class RedemptionRequest:
    id: int
    pool_id: int
    user_id: int
    # None = todo lo que cumpla la permanencia
    amount: Decimal | None
    status: str = "queued"
    note: str | None = None
    settlement_id: int | None = None
    created_by_user_id: int | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    def belongs_to(self, user_id: int) -> bool:
        return self.user_id == int(user_id)


@dataclass
class SettlementRedemption:
    id: int
    settlement_id: int
    redemption_request_id: int
    pool_id: int
    user_id: int
    units: Decimal
    value: Decimal
    cost: Decimal
    gain: Decimal
    return_pct: Decimal
    fee: Decimal
    net: Decimal
    # Lo pedido que no salió (no cumplía la permanencia); None = salió todo
    pending_amount: Decimal | None
    fee_schedule_id: int | None
    commission_version_id: int | None
    breakdown: list[dict[str, str | None]] = field(default_factory=list)
    created_at: datetime | None = None


@dataclass
class CommissionCredit:
    id: int
    settlement_redemption_id: int
    user_id: int
    amount: Decimal
    created_at: datetime | None = None
