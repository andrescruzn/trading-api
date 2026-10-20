# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/billing/settle_fee_transaction_service.py
#
# CASO DE USO:
# - El admin registra qué pasó con una comisión pendiente: se cobró
#   (`charged`, con fecha) o se condonó (`waived`, con nota opcional).
#
# REGLAS:
# - Solo una comisión `pending` cambia de estado (FEE_TX_NOT_PENDING si no).
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.billing.domain.fee_transaction_entity import FeeTransaction
from app.modules.billing.domain.fee_transaction_repository import FeeTransactionRepository


class SettleFeeTransactionService:
    """Marca una comisión pendiente como cobrada o condonada."""

    def __init__(self, fee_tx_repo: FeeTransactionRepository):
        self._fee_tx_repo = fee_tx_repo

    def execute(
        self,
        fee_tx_id: int,
        action: str,
        notes: str | None = None,
    ) -> ServiceResult[FeeTransaction]:
        if action not in ("charge", "waive"):
            return ServiceResult.fail(code="FEE_TX_INVALID_ACTION", http_status=422)

        fee_tx = self._fee_tx_repo.find_by_id(fee_tx_id)
        if fee_tx is None:
            return ServiceResult.fail(code="FEE_TX_NOT_FOUND", http_status=404)
        if not fee_tx.is_pending():
            return ServiceResult.fail(
                code="FEE_TX_NOT_PENDING", http_status=409, meta={"status": fee_tx.status}
            )

        if action == "charge":
            fee_tx.mark_as_charged(utc_now())
            if notes:
                fee_tx.notes = notes
        else:
            fee_tx.waive(notes)

        fee_tx = self._fee_tx_repo.update(fee_tx)
        self._fee_tx_repo.commit()
        return ServiceResult.ok(data=fee_tx)
