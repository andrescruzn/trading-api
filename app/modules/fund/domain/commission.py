# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/commission.py
#
# Comisión del fondo común (F5), en funciones puras:
#
# - Tabla de tramos (FeeSchedule): cada tramo de RETORNO paga su % sobre la
#   ganancia de ese tramo, como los impuestos. Ganar más nunca deja menos
#   neto (decisión del usuario, 2026-10-22). Versionada: cambiarla no
#   reescribe redenciones pasadas.
#     Ej.: 0 %→10 %, 50 %→15 %, 100 %→20 %. Aportó 1.000, vale 3.000
#     (+200 %): 500×10 % + 500×15 % + 1.000×20 % = 325.
# - Reparto (CommissionShareVersion): qué % de cada comisión recibe cada
#   propietario (super admin y socios). Suma 100 %. Versionado.
#
# Todos pagan comisión, también los propietarios por su capital propio
# (decisión del usuario): su comisión entra al reparto como la de cualquiera.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_DOWN, Decimal

PRECISION = Decimal("0.000000000001")
MAX_TIERS = 10
_ZERO = Decimal("0")
_ONE = Decimal("1")


# ======================================================================
# Tramos
# ======================================================================

@dataclass(frozen=True)
class FeeTier:
    """Desde este retorno (fracción: 0.5 = 50 %) se cobra `rate` (fracción)."""

    from_return: Decimal
    rate: Decimal


@dataclass
class FeeSchedule:
    id: int
    tiers: list[FeeTier]
    note: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime | None = None


def valid_tiers(tiers: list[FeeTier]) -> bool:
    """El primer tramo arranca en 0 %, los demás crecen y cada tasa va de 0 a 100 %."""
    if not 1 <= len(tiers) <= MAX_TIERS or tiers[0].from_return != 0:
        return False
    for previous, current in zip(tiers, tiers[1:]):
        if current.from_return <= previous.from_return:
            return False
    return all(_ZERO <= t.rate <= _ONE for t in tiers)


@dataclass(frozen=True)
class TierCharge:
    """Lo que cobró un tramo: base = parte de la ganancia que cae en él."""

    from_return: Decimal
    to_return: Decimal | None
    rate: Decimal
    base: Decimal
    fee: Decimal


def tiered_fee(cost: Decimal, gain: Decimal, tiers: list[FeeTier]) -> tuple[Decimal, list[TierCharge]]:
    """Comisión escalonada sobre `gain` (retorno = gain / cost). Sin ganancia, 0."""
    if gain <= 0 or cost <= 0 or not tiers:
        return _ZERO, []
    ret = gain / cost
    total = _ZERO
    charges: list[TierCharge] = []
    for index, tier in enumerate(tiers):
        if ret <= tier.from_return:
            break
        upper = tiers[index + 1].from_return if index + 1 < len(tiers) else None
        top = ret if upper is None else min(ret, upper)
        base = (cost * (top - tier.from_return)).quantize(PRECISION)
        fee = (base * tier.rate).quantize(PRECISION, rounding=ROUND_DOWN)
        total += fee
        charges.append(TierCharge(tier.from_return, upper, tier.rate, base, fee))
    return total, charges


# ======================================================================
# Reparto entre propietarios
# ======================================================================

@dataclass(frozen=True)
class CommissionShare:
    user_id: int
    pct: Decimal


@dataclass
class CommissionShareVersion:
    id: int
    shares: list[CommissionShare] = field(default_factory=list)
    note: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime | None = None


def valid_shares(shares: list[CommissionShare]) -> bool:
    """Al menos uno, sin repetir, cada % > 0 y suman exactamente 100 %."""
    if not shares or len({s.user_id for s in shares}) != len(shares):
        return False
    if any(s.pct <= 0 for s in shares):
        return False
    return sum((s.pct for s in shares), _ZERO) == _ONE


def split_commission(fee: Decimal, shares: list[CommissionShare]) -> list[tuple[int, Decimal]]:
    """
    Reparte `fee` según los %. Se redondea hacia abajo y el residuo va al
    propietario de menor id: la suma de las partes es exactamente `fee`.
    """
    if fee <= 0 or not shares:
        return []
    ordered = sorted(shares, key=lambda s: s.user_id)
    parts = [(s.user_id, (fee * s.pct).quantize(PRECISION, rounding=ROUND_DOWN)) for s in ordered]
    residual = fee - sum((amount for _, amount in parts), _ZERO)
    first_user, first_amount = parts[0]
    parts[0] = (first_user, first_amount + residual)
    return [(user_id, amount) for user_id, amount in parts if amount > 0]
