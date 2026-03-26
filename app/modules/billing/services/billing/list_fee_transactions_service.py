# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/billing/list_fee_transactions_service.py
# ======================================================================

from __future__ import annotations

from app.common.contracts.service_result import ServiceResult
from app.modules.billing.domain.fee_transaction_entity import FeeTransaction
from app.modules.billing.domain.fee_transaction_repository import FeeTransactionRepository
from app.modules.billing.domain.managed_account_repository import ManagedAccountRepository


class ListFeeTransactionsService:
    """
    Lista las transacciones de fee de una cuenta gestionada.
    Verifica ownership si se pasa investor_id.
    """

    def __init__(
        self,
        fee_tx_repo: FeeTransactionRepository,
        managed_account_repo: ManagedAccountRepository,
    ):
        self._fee_tx_repo = fee_tx_repo
        self._managed_account_repo = managed_account_repo

    def execute(
        self,
        managed_account_id: int,
        investor_id: int | None = None,
        limit: int = 50,
    ) -> ServiceResult[list[FeeTransaction]]:
        account = self._managed_account_repo.find_by_id(managed_account_id)
        if not account:
            return ServiceResult.fail(
                code="BILLING_MANAGED_ACCOUNT_NOT_FOUND",
                http_status=404,
            )

        if investor_id is not None and account.investor_id != investor_id:
            return ServiceResult.fail(
                code="BILLING_MANAGED_ACCOUNT_FORBIDDEN",
                http_status=403,
            )

        txs = self._fee_tx_repo.list_by_managed_account(managed_account_id, limit=limit)
        return ServiceResult.ok(data=txs)
