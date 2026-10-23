# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/deposit_request_entity.py
#
# Entidad de dominio: DepositRequest (solicitud de depósito al fondo).
#
# FLUJO:
#   pending  → el participante envió USDT y registró el txid; se espera a
#              que el depósito aparezca en el exchange.
#   review   → apareció, pero un super admin debe decidir (monto distinto
#              al declarado, por encima del tope, o fallido en el exchange).
#   confirmed→ acreditado al saldo pendiente de asignar (asiento `deposit`).
#   rejected → un super admin lo rechazó (con motivo).
#   expired  → nunca apareció en el exchange antes de `expires_at`.
#   canceled → el participante la anuló antes de que se resolviera.
#
# REGLAS:
# - Se acredita lo que reporta el exchange (`credited_amount`), no lo
#   declarado.
# - El txid es único en todo el fondo: nadie reclama dos veces el mismo
#   depósito, ni el depósito de otra persona que ya lo registró.
# ======================================================================

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

DEPOSIT_STATUSES = ("pending", "review", "confirmed", "rejected", "expired", "canceled")
OPEN_DEPOSIT_STATUSES = ("pending", "review")

# Por qué una solicitud quedó en revisión
DEPOSIT_REVIEW_REASONS = ("amount_mismatch", "over_threshold", "exchange_failed", "wrong_asset")

# Diferencia aceptada entre lo declarado y lo acreditado (redondeos del
# exchange); más que esto pasa a revisión.
AMOUNT_TOLERANCE_RATIO = Decimal("0.01")

_HEX_TXID = re.compile(r"^(0[xX])?[0-9a-fA-F]+$")
_VALID_TXID = re.compile(r"^[A-Za-z0-9:_\-]{10,128}$")


def normalize_txid(raw: str) -> str:
    """
    Quita espacios y, si el txid es hexadecimal (Tron, EVM), lo pasa a
    minúsculas: en esas redes la misma transacción se puede escribir con
    mayúsculas o minúsculas. Otros formatos (p. ej. Solana, base58)
    distinguen mayúsculas y se dejan tal cual.
    """
    txid = (raw or "").strip()
    return txid.lower() if _HEX_TXID.match(txid) else txid


def is_valid_txid(txid: str) -> bool:
    return bool(_VALID_TXID.match(txid))


def amounts_match(declared: Decimal, credited: Decimal) -> bool:
    """True si lo acreditado está dentro de la tolerancia de lo declarado."""
    if declared <= 0:
        return False
    return abs(credited - declared) <= declared * AMOUNT_TOLERANCE_RATIO


@dataclass
class DepositRequest:
    id: int
    user_id: int
    asset: str
    network: str
    txid: str
    declared_amount: Decimal
    status: str = "pending"
    credited_amount: Decimal | None = None
    address_from: str | None = None
    exchange_deposit_id: str | None = None
    exchange_status: str | None = None
    review_reason: str | None = None
    resolved_by_user_id: int | None = None
    resolved_at: datetime | None = None
    resolution_note: str | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_open(self) -> bool:
        return self.status in OPEN_DEPOSIT_STATUSES

    def is_expired(self, now: datetime) -> bool:
        return self.status == "pending" and self.expires_at is not None and self.expires_at <= now

    def belongs_to(self, user_id: int) -> bool:
        return self.user_id == int(user_id)

    def amount_to_credit(self) -> Decimal:
        """Lo que entra al saldo: lo del exchange si se conoce; si no, lo declarado."""
        return self.credited_amount if self.credited_amount is not None else self.declared_amount
