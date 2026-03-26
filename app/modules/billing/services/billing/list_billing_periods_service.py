# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/billing/list_billing_periods_service.py
# ======================================================================

from __future__ import annotations

from app.common.contracts.service_result import ServiceResult
from app.modules.billing.domain.billing_period_entity import BillingPeriod
from app.modules.billing.domain.billing_period_repository import BillingPeriodRepository
from app.modules.billing.domain.managed_account_repository import ManagedAccountRepository


class ListBillingPeriodsService:
    """
    Lista los períodos de facturación de una cuenta gestionada.
    Verifica ownership si se pasa investor_id (para rol investor).
    """

    def __init__(
        self,
        period_repo: BillingPeriodRepository,
        managed_account_repo: ManagedAccountRepository,
    ):
        self._period_repo = period_repo
        self._managed_account_repo = managed_account_repo

    def execute(
        self,
        managed_account_id: int,
        investor_id: int | None = None,
        limit: int = 50,
    ) -> ServiceResult[list[BillingPeriod]]:
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

        periods = self._period_repo.list_by_managed_account(managed_account_id, limit=limit)
        return ServiceResult.ok(data=periods)
