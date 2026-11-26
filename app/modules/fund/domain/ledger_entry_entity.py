# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/ledger_entry_entity.py
#
# Entidad de dominio: LedgerEntry (libro mayor del fondo común).
#
# REGLAS DE NEGOCIO:
# - El libro es append-only: un asiento nunca se edita ni se borra. Para
#   corregir se registra otro asiento.
# - El saldo de una persona es la suma de sus asientos, por "bucket":
#   · pending   = pendiente de asignar: depósito confirmado que aún no pasó
#                 por un agente. No se puede retirar.
#   · available = disponible: viene de un agente o de comisiones. Sí se
#                 puede retirar (se usa desde la F4).
# - `amount` lleva signo: + entra al bucket, − sale.
# - Un asiento ligado a otra cosa (`ref_type`, `ref_id`) es único por tipo:
#   la misma solicitud nunca se acredita dos veces (índice único en la BD).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

LEDGER_BUCKETS = ("pending", "available")

# Tipos de asiento. F3: depósito y devolución. F4: asignación a un agente
# (sale del saldo pendiente o disponible y se convierte en unidades). F5:
# redemption (sale de un agente, entra al disponible), fee (la comisión que
# paga quien sale), commission (la parte de un propietario) y withdrawal
# (retiro enviado a la dirección cripto de la persona).
LEDGER_ENTRY_TYPES = (
    "deposit",
    "refund",
    "allocation",
    "redemption",
    "fee",
    "commission",
    "withdrawal",
)


@dataclass(frozen=True)
class LedgerEntry:
    id: int
    user_id: int
    entry_type: str
    bucket: str
    amount: Decimal
    asset: str
    ref_type: str | None = None
    ref_id: int | None = None
    bot_id: int | None = None
    description: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class FundBalances:
    """Saldos de una persona en el fondo (suma de su libro)."""

    user_id: int
    pending: Decimal
    available: Decimal

    @property
    def total(self) -> Decimal:
        return self.pending + self.available
