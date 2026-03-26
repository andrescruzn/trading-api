# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/managed_accounts/update_managed_account_service.py
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.contracts.service_result import ServiceResult
from app.modules.billing.domain.managed_account_entity import ManagedAccount
from app.modules.billing.domain.managed_account_repository import ManagedAccountRepository


class UpdateManagedAccountService:
    """Actualiza nombre, bot_id, period_type y/o is_active de una cuenta gestionada."""

    def __init__(self, repo: ManagedAccountRepository, session: Session):
        self._repo = repo
        self._session = session

    def execute(
        self,
        managed_account_id: int,
        name: str | None = None,
        bot_id: int | None = None,
        period_type: str | None = None,
        is_active: bool | None = None,
    ) -> ServiceResult[ManagedAccount]:
        account = self._repo.find_by_id(managed_account_id)
        if not account:
            return ServiceResult.fail(
                code="BILLING_MANAGED_ACCOUNT_NOT_FOUND",
                http_status=404,
            )

        if period_type is not None and period_type not in ManagedAccount.VALID_PERIOD_TYPES:
            return ServiceResult.fail(
                code="BILLING_INVALID_PERIOD_TYPE",
                http_status=422,
            )

        if name is not None:
            account.name = name
        if bot_id is not None:
            account.bot_id = bot_id
        if period_type is not None:
            account.period_type = period_type
        if is_active is not None:
            account.is_active = is_active

        saved = self._repo.save(account)
        self._session.commit()
        return ServiceResult.ok(data=saved)
