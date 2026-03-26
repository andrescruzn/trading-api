# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/billing/open_billing_period_service.py
#
# Abre un nuevo período de facturación para una cuenta gestionada.
# Solo se puede tener UN período abierto por cuenta a la vez.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.contracts.service_result import ServiceResult
from app.modules.billing.domain.billing_period_entity import BillingPeriod
from app.modules.billing.domain.billing_period_repository import BillingPeriodRepository
from app.modules.billing.domain.investor_repository import InvestorRepository
from app.modules.billing.domain.managed_account_repository import ManagedAccountRepository


class OpenBillingPeriodService:
    """
    Abre un nuevo período de facturación.

    Reglas:
    - La cuenta gestionada debe existir y estar activa.
    - No puede haber un período 'open' previo (debe cerrarse primero).
    - opening_equity es el equity actual de la cuenta (lo provee el llamador).
    - fee_pct se toma como snapshot del inversor en el momento de apertura.
    """

    def __init__(
        self,
        period_repo: BillingPeriodRepository,
        managed_account_repo: ManagedAccountRepository,
        investor_repo: InvestorRepository,
        session: Session,
    ):
        self._period_repo = period_repo
        self._managed_account_repo = managed_account_repo
        self._investor_repo = investor_repo
        self._session = session

    def execute(
        self,
        managed_account_id: int,
        opening_equity: Decimal,
    ) -> ServiceResult[BillingPeriod]:
        # Verificar que la cuenta existe y está activa
        account = self._managed_account_repo.find_by_id(managed_account_id)
        if not account:
            return ServiceResult.fail(
                code="BILLING_MANAGED_ACCOUNT_NOT_FOUND",
                http_status=404,
            )
        if not account.is_active:
            return ServiceResult.fail(
                code="BILLING_MANAGED_ACCOUNT_INACTIVE",
                http_status=422,
            )

        # Verificar que no haya un período abierto
        existing_open = self._period_repo.find_open_by_managed_account(managed_account_id)
        if existing_open:
            return ServiceResult.fail(
                code="BILLING_PERIOD_ALREADY_OPEN",
                http_status=409,
            )

        # Tomar snapshot del fee_pct actual del inversor
        investor = self._investor_repo.find_by_id(account.investor_id)
        fee_pct = investor.fee_pct if investor else Decimal("0")

        period = BillingPeriod(
            id=0,
            managed_account_id=managed_account_id,
            opening_equity=opening_equity,
            fee_pct=fee_pct,
            status=BillingPeriod.STATUS_OPEN,
        )

        saved = self._period_repo.save(period)
        self._session.commit()
        return ServiceResult.ok(data=saved)
