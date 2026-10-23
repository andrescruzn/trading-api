# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/withdrawal_entity.py
#
# Retiros del fondo común (F5):
#
# - PayoutMethod      → a dónde se le paga a una persona (banco o Nequi). Los
#                       datos van cifrados; en pantalla solo un resumen
#                       enmascarado. Un medio nuevo espera un tiempo antes de
#                       usarse (si alguien toma la cuenta, no puede desviar
#                       un retiro al instante).
# - WithdrawalRequest → "págame X USDT de mi saldo disponible". Un super admin
#                       paga por fuera (vende USDT, transfiere COP) y la marca
#                       pagada con el monto en COP, la tasa y la referencia.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

PAYOUT_KINDS = ("bank", "nequi")
WITHDRAWAL_STATUSES = ("requested", "paid", "rejected", "canceled")

# Campos de los datos de cada tipo (los que el formulario pide)
PAYOUT_FIELDS: dict[str, tuple[str, ...]] = {
    "bank": ("holder_name", "document_number", "bank_name", "account_type", "account_number"),
    "nequi": ("holder_name", "document_number", "phone"),
}


def mask_payout(kind: str, details: dict[str, str]) -> str:
    """`Bancolombia · ahorros ···1234` / `Nequi ···7890` (sin datos completos)."""
    if kind == "nequi":
        return f"Nequi ···{(details.get('phone') or '')[-4:]}"
    bank = details.get("bank_name") or "Banco"
    account_type = details.get("account_type") or ""
    number = (details.get("account_number") or "")[-4:]
    return " · ".join(part for part in (bank, account_type, f"···{number}") if part)


@dataclass
class PayoutMethod:
    id: int
    user_id: int
    kind: str
    label: str
    masked: str
    usable_from: datetime
    is_active: bool = True
    # Solo en memoria (descifrados) cuando un super admin va a pagar
    details: dict[str, str] = field(default_factory=dict)
    created_at: datetime | None = None

    def is_usable(self, now: datetime) -> bool:
        return self.is_active and self.usable_from <= now

    def belongs_to(self, user_id: int) -> bool:
        return self.user_id == int(user_id)


@dataclass
class WithdrawalRequest:
    id: int
    user_id: int
    amount: Decimal
    payout_method_id: int
    status: str = "requested"
    paid_cop_amount: Decimal | None = None
    cop_rate: Decimal | None = None
    payment_reference: str | None = None
    resolution_note: str | None = None
    resolved_by_user_id: int | None = None
    resolved_at: datetime | None = None
    created_at: datetime | None = None

    def belongs_to(self, user_id: int) -> bool:
        return self.user_id == int(user_id)
