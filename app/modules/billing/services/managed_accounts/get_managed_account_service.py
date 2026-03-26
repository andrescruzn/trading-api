# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/managed_accounts/get_managed_account_service.py
# ======================================================================

from __future__ import annotations

from app.common.contracts.service_result import ServiceResult
from app.modules.billing.domain.managed_account_entity import ManagedAccount
from app.modules.billing.domain.managed_account_repository import ManagedAccountRepository


class GetManagedAccountService:
    """Obtiene una cuenta gestionada por ID. Incluye ownership check para investor."""

    def __init__(self, repo: ManagedAccountRepository):
        self._repo = repo

    def execute(
        self,
        managed_account_id: int,
        investor_id: int | None = None,
    ) -> ServiceResult[ManagedAccount]:
        account = self._repo.find_by_id(managed_account_id)
        if not account:
            return ServiceResult.fail(
                code="BILLING_MANAGED_ACCOUNT_NOT_FOUND",
                http_status=404,
            )

        # Si se pasa investor_id, verificar ownership
        if investor_id is not None and account.investor_id != investor_id:
            return ServiceResult.fail(
                code="BILLING_MANAGED_ACCOUNT_FORBIDDEN",
                http_status=403,
            )

        return ServiceResult.ok(data=account)
