# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/managed_accounts/list_managed_accounts_service.py
# ======================================================================

from __future__ import annotations

from app.common.contracts.service_result import ServiceResult
from app.modules.billing.domain.managed_account_entity import ManagedAccount
from app.modules.billing.domain.managed_account_repository import ManagedAccountRepository


class ListManagedAccountsService:
    """
    Lista cuentas gestionadas.
    - Admin: ve todas.
    - Investor: ve solo las de su investor_id.
    """

    def __init__(self, repo: ManagedAccountRepository):
        self._repo = repo

    def execute(
        self,
        investor_id: int | None = None,
        only_active: bool = False,
    ) -> ServiceResult[list[ManagedAccount]]:
        if investor_id is not None:
            accounts = self._repo.list_by_investor(investor_id)
            if only_active:
                accounts = [a for a in accounts if a.is_active]
        else:
            accounts = self._repo.list_all(only_active=only_active)

        return ServiceResult.ok(data=accounts)
