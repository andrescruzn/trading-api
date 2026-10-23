# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/providers/fund_provider.py
#
# Factory de los servicios del fondo común (F3: ajustes, libro mayor y
# depósitos). Reutiliza de M4 la billetera de la plataforma, sus cuentas y
# el gateway del exchange; de M1, el repositorio de usuarios.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.security.credentials_cipher import CredentialsCipher
from app.modules.accounts.infrastructure import (
    SqlAlchemyAccountRepository,
    SqlAlchemyPlatformWalletRepository,
)
from app.modules.accounts.infrastructure.ccxt_wallet_gateway import CcxtWalletGateway
from app.modules.fund.infrastructure import (
    SqlAlchemyDepositRequestRepository,
    SqlAlchemyFundSettingsRepository,
    SqlAlchemyLedgerRepository,
)
from app.modules.fund.services.deposits import (
    CreateDepositRequestService,
    ResolveDepositRequestService,
    UnclaimedDepositsService,
    VerifyDepositsService,
)
from app.modules.fund.services.ledger import FundLedgerService
from app.modules.fund.services.settings import DepositNetworksService, FundSettingsService
from app.modules.fund.services.wallet_context import WalletContextResolver
from app.modules.market.infrastructure import SqlAlchemyExchangeRepository
from app.modules.users.infrastructure import SqlAlchemyUserRepository


class FundServiceFactory:
    """Todos los repos comparten la sesión: un commit confirma todo el caso de uso."""

    def __init__(self, session: Session):
        self._session = session
        self._settings_repo = SqlAlchemyFundSettingsRepository(session)
        self._ledger_repo = SqlAlchemyLedgerRepository(session)
        self._deposit_repo = SqlAlchemyDepositRequestRepository(session)
        self._user_repo = SqlAlchemyUserRepository(session)
        self._wallet_resolver = WalletContextResolver(
            wallet_repo=SqlAlchemyPlatformWalletRepository(session),
            account_repo=SqlAlchemyAccountRepository(session),
        )

    def _gateway(self) -> CcxtWalletGateway:
        # Solo se arma cuando el caso de uso habla con el exchange
        return CcxtWalletGateway(
            exchange_repo=SqlAlchemyExchangeRepository(self._session),
            cipher=CredentialsCipher.from_settings(),
        )

    # ------------------------------------------------------------------
    # Ajustes
    # ------------------------------------------------------------------

    def fund_settings(self) -> FundSettingsService:
        return FundSettingsService(
            settings_repo=self._settings_repo, wallet_resolver=self._wallet_resolver
        )

    def deposit_networks(self) -> DepositNetworksService:
        return DepositNetworksService(
            settings_repo=self._settings_repo,
            wallet_resolver=self._wallet_resolver,
            gateway=self._gateway(),
        )

    # ------------------------------------------------------------------
    # Depósitos
    # ------------------------------------------------------------------

    def create_deposit_request(self) -> CreateDepositRequestService:
        return CreateDepositRequestService(
            deposit_repo=self._deposit_repo,
            settings_repo=self._settings_repo,
            wallet_resolver=self._wallet_resolver,
        )

    def resolve_deposit_request(self) -> ResolveDepositRequestService:
        return ResolveDepositRequestService(
            deposit_repo=self._deposit_repo, ledger_repo=self._ledger_repo
        )

    def verify_deposits(self) -> VerifyDepositsService:
        return VerifyDepositsService(
            deposit_repo=self._deposit_repo,
            ledger_repo=self._ledger_repo,
            settings_repo=self._settings_repo,
            wallet_resolver=self._wallet_resolver,
            gateway=self._gateway(),
        )

    def unclaimed_deposits(self) -> UnclaimedDepositsService:
        return UnclaimedDepositsService(
            deposit_repo=self._deposit_repo,
            ledger_repo=self._ledger_repo,
            user_repo=self._user_repo,
            wallet_resolver=self._wallet_resolver,
            gateway=self._gateway(),
        )

    # ------------------------------------------------------------------
    # Libro mayor
    # ------------------------------------------------------------------

    def ledger(self) -> FundLedgerService:
        return FundLedgerService(
            ledger_repo=self._ledger_repo,
            user_repo=self._user_repo,
            asset=settings.WALLET_BASE_ASSET,
        )
