# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/providers/account_provider.py
#
# Factory que centraliza la creación de todos los servicios del módulo
# Accounts & Portfolio. Sigue el mismo patrón que MarketServiceFactory.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.security.credentials_cipher import CredentialsCipher
from app.modules.accounts.infrastructure import (
    SqlAlchemyAccountRepository,
    SqlAlchemyAccountBalanceRepository,
)
from app.modules.accounts.services.accounts import (
    ListAccountsService,
    GetAccountService,
    CreateAccountService,
    UpdateAccountService,
)
from app.modules.accounts.services.balances import (
    ListBalancesService,
    RecordBalanceService,
)
from app.modules.market.infrastructure import SqlAlchemyExchangeRepository


class AccountServiceFactory:
    """
    Factory para todos los servicios del módulo Accounts & Portfolio.

    Uso en routes:
        factory = AccountServiceFactory(session=db)
        result = factory.list_accounts().list(user_id=1)
    """

    def __init__(self, session: Session):
        self._session = session

        # Repositorios del módulo
        self._account_repo = SqlAlchemyAccountRepository(session)
        self._balance_repo = SqlAlchemyAccountBalanceRepository(session)

        # Repositorio externo (market) para validar exchange_id
        self._exchange_repo = SqlAlchemyExchangeRepository(session)

        # Cipher para credenciales
        self._cipher = CredentialsCipher(settings.CREDENTIALS_SECRET_KEY)

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------

    def list_accounts(self) -> ListAccountsService:
        return ListAccountsService(repo=self._account_repo)

    def get_account(self) -> GetAccountService:
        return GetAccountService(repo=self._account_repo)

    def create_account(self) -> CreateAccountService:
        return CreateAccountService(
            account_repo=self._account_repo,
            exchange_repo=self._exchange_repo,
            session=self._session,
            cipher=self._cipher,
        )

    def update_account(self) -> UpdateAccountService:
        return UpdateAccountService(
            account_repo=self._account_repo,
            exchange_repo=self._exchange_repo,
            session=self._session,
            cipher=self._cipher,
        )

    # ------------------------------------------------------------------
    # Balances
    # ------------------------------------------------------------------

    def list_balances(self) -> ListBalancesService:
        return ListBalancesService(
            account_repo=self._account_repo,
            balance_repo=self._balance_repo,
        )

    def record_balance(self) -> RecordBalanceService:
        return RecordBalanceService(
            account_repo=self._account_repo,
            balance_repo=self._balance_repo,
            session=self._session,
        )


# ======================================================================
# Dependency para FastAPI
# ======================================================================

def get_account_factory(session: Session) -> AccountServiceFactory:
    return AccountServiceFactory(session=session)
