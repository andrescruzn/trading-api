# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/providers/billing_provider.py
#
# Factory para todos los servicios del módulo Billing.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.billing.infrastructure import (
    SqlAlchemyInvestorRepository,
    SqlAlchemyManagedAccountRepository,
    SqlAlchemyBillingPeriodRepository,
    SqlAlchemyFeeTransactionRepository,
)
from app.modules.billing.services.investors import (
    ListInvestorsService,
    CreateInvestorService,
    UpdateInvestorService,
)
from app.modules.billing.services.managed_accounts import (
    ListManagedAccountsService,
    GetManagedAccountService,
    CreateManagedAccountService,
    UpdateManagedAccountService,
)
from app.modules.billing.services.billing import (
    ListBillingPeriodsService,
    OpenBillingPeriodService,
    CloseBillingPeriodService,
    ListFeeTransactionsService,
)


class BillingServiceFactory:
    """
    Factory para todos los servicios del módulo Billing.

    Instancia los 4 repositorios propios y expone un método por servicio,
    siguiendo el mismo patrón que AlertServiceFactory, BotServiceFactory, etc.
    """

    def __init__(self, session: Session):
        self._session = session

        # Repositorios propios
        self._investor_repo = SqlAlchemyInvestorRepository(session)
        self._managed_account_repo = SqlAlchemyManagedAccountRepository(session)
        self._period_repo = SqlAlchemyBillingPeriodRepository(session)
        self._fee_tx_repo = SqlAlchemyFeeTransactionRepository(session)

    # ------------------------------------------------------------------
    # Investors
    # ------------------------------------------------------------------

    def list_investors(self) -> ListInvestorsService:
        return ListInvestorsService(repo=self._investor_repo)

    def create_investor(self) -> CreateInvestorService:
        return CreateInvestorService(
            repo=self._investor_repo,
            session=self._session,
        )

    def update_investor(self) -> UpdateInvestorService:
        return UpdateInvestorService(
            repo=self._investor_repo,
            session=self._session,
        )

    # ------------------------------------------------------------------
    # Managed Accounts
    # ------------------------------------------------------------------

    def list_managed_accounts(self) -> ListManagedAccountsService:
        return ListManagedAccountsService(repo=self._managed_account_repo)

    def get_managed_account(self) -> GetManagedAccountService:
        return GetManagedAccountService(repo=self._managed_account_repo)

    def create_managed_account(self) -> CreateManagedAccountService:
        return CreateManagedAccountService(
            investor_repo=self._investor_repo,
            managed_account_repo=self._managed_account_repo,
            session=self._session,
        )

    def update_managed_account(self) -> UpdateManagedAccountService:
        return UpdateManagedAccountService(
            repo=self._managed_account_repo,
            session=self._session,
        )

    # ------------------------------------------------------------------
    # Billing Periods
    # ------------------------------------------------------------------

    def list_billing_periods(self) -> ListBillingPeriodsService:
        return ListBillingPeriodsService(
            period_repo=self._period_repo,
            managed_account_repo=self._managed_account_repo,
        )

    def open_billing_period(self) -> OpenBillingPeriodService:
        return OpenBillingPeriodService(
            period_repo=self._period_repo,
            managed_account_repo=self._managed_account_repo,
            investor_repo=self._investor_repo,
            session=self._session,
        )

    def close_billing_period(self) -> CloseBillingPeriodService:
        return CloseBillingPeriodService(
            period_repo=self._period_repo,
            fee_tx_repo=self._fee_tx_repo,
            managed_account_repo=self._managed_account_repo,
            session=self._session,
        )

    def list_fee_transactions(self) -> ListFeeTransactionsService:
        return ListFeeTransactionsService(
            fee_tx_repo=self._fee_tx_repo,
            managed_account_repo=self._managed_account_repo,
        )


def get_billing_factory(session: Session) -> BillingServiceFactory:
    """Dependency FastAPI para inyectar el factory en los routes."""
    return BillingServiceFactory(session=session)
