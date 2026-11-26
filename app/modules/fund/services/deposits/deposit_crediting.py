# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/deposits/deposit_crediting.py
#
# PROPÓSITO:
# - Un solo camino para pasar una solicitud a `confirmed` y acreditarla al
#   saldo pendiente de asignar. Lo usan la verificación automática, la
#   confirmación de un super admin y la asignación de un depósito sin
#   reclamar.
#
# REGLA:
# - Primero el UPDATE condicional (solo si la solicitud sigue en uno de los
#   estados esperados); el asiento solo se crea si ese UPDATE ganó. Así dos
#   procesos a la vez nunca acreditan dos veces. Además, el índice único
#   del libro (entry_type, ref_type, ref_id) lo impide en la BD.
# - No hace commit: lo decide el caso de uso.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.modules.fund.domain.deposit_request_entity import DepositRequest
from app.modules.fund.domain.fund_repositories import DepositRequestRepository, LedgerRepository
from app.modules.fund.domain.ledger_entry_entity import LedgerEntry

DEPOSIT_REF_TYPE = "deposit_request"


class DepositCreditor:

    def __init__(self, deposit_repo: DepositRequestRepository, ledger_repo: LedgerRepository):
        self._deposit_repo = deposit_repo
        self._ledger_repo = ledger_repo

    def confirm(
        self,
        request: DepositRequest,
        *,
        amount: Decimal,
        now: datetime,
        expected: list[str],
        resolved_by_user_id: int | None,
        note: str | None,
    ) -> bool:
        """True si esta llamada confirmó y acreditó la solicitud."""
        request.status = "confirmed"
        request.credited_amount = amount
        request.resolved_at = now
        request.resolved_by_user_id = resolved_by_user_id
        request.resolution_note = note
        if not self._deposit_repo.update_if_status(request, expected):
            return False

        self._ledger_repo.add(
            LedgerEntry(
                id=0,
                user_id=request.user_id,
                entry_type="deposit",
                bucket="pending",
                amount=amount,
                asset=request.asset,
                ref_type=DEPOSIT_REF_TYPE,
                ref_id=request.id,
                description=f"Depósito {request.network} · {request.txid}",
                created_by_user_id=resolved_by_user_id,
            )
        )
        return True
