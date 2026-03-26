# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/managed_accounts/create_managed_account_service.py
#
# Crea una nueva cuenta gestionada.
# El HWM inicial se establece igual al initial_capital.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.contracts.service_result import ServiceResult
from app.modules.billing.domain.managed_account_entity import ManagedAccount
from app.modules.billing.domain.investor_repository import InvestorRepository
from app.modules.billing.domain.managed_account_repository import ManagedAccountRepository


class CreateManagedAccountService:
    """
    Crea una cuenta gestionada para un inversor.

    Reglas de negocio:
    - El inversor debe existir y estar activo.
    - El period_type debe ser válido (daily | weekly | monthly).
    - El HWM inicial = initial_capital (el primer período parte desde el capital inicial).
    """

    def __init__(
        self,
        investor_repo: InvestorRepository,
        managed_account_repo: ManagedAccountRepository,
        session: Session,
    ):
        self._investor_repo = investor_repo
        self._managed_account_repo = managed_account_repo
        self._session = session

    def execute(
        self,
        investor_id: int,
        account_id: int,
        name: str,
        initial_capital: Decimal,
        period_type: str = "monthly",
        bot_id: int | None = None,
    ) -> ServiceResult[ManagedAccount]:
        # Verificar que el inversor existe y está activo
        investor = self._investor_repo.find_by_id(investor_id)
        if not investor:
            return ServiceResult.fail(
                code="BILLING_INVESTOR_NOT_FOUND",
                http_status=404,
            )
        if not investor.is_active:
            return ServiceResult.fail(
                code="BILLING_INVESTOR_INACTIVE",
                http_status=422,
            )

        # Validar period_type
        if period_type not in ManagedAccount.VALID_PERIOD_TYPES:
            return ServiceResult.fail(
                code="BILLING_INVALID_PERIOD_TYPE",
                http_status=422,
            )

        if initial_capital < Decimal("0"):
            return ServiceResult.fail(
                code="BILLING_INVALID_CAPITAL",
                http_status=422,
            )

        managed_account = ManagedAccount(
            id=0,
            investor_id=investor_id,
            account_id=account_id,
            bot_id=bot_id,
            name=name,
            initial_capital=initial_capital,
            # HWM inicial = capital inicial.
            # La primera ganancia real se mide contra este valor.
            high_water_mark=initial_capital,
            period_type=period_type,
        )

        saved = self._managed_account_repo.save(managed_account)
        self._session.commit()
        return ServiceResult.ok(data=saved)
