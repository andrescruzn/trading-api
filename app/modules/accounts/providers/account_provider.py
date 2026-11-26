# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/providers/account_provider.py
#
# Factory que centraliza la creación de los servicios del módulo
# Accounts & Portfolio: hoy, la billetera única de Binance. Las cuentas
# (`accounts`) son un detalle interno: la de la billetera y las de
# práctica de cada agente demo; nadie las maneja desde la API.
#
# `build_platform_wallet_ensurer(session)` lo usan otros módulos (bots,
# fondo) para asegurar la billetera sin armar toda la factory.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.modules.accounts.infrastructure import (
    SqlAlchemyAccountRepository,
    SqlAlchemyAccountBalanceRepository,
    SqlAlchemyPlatformWalletRepository,
    SqlAlchemyWalletSnapshotRepository,
)
from app.modules.accounts.infrastructure.ccxt_wallet_gateway import CcxtWalletGateway
from app.modules.accounts.infrastructure.exchange_client import platform_credentials_configured
from app.modules.accounts.services.wallet import (
    EnsurePlatformWalletService,
    GetWalletService,
    SyncWalletService,
)
from app.modules.market.infrastructure import SqlAlchemyExchangeRepository


def _first_super_admin_id(session: Session):
    """Resolver del dueño de la cuenta de la billetera: el primer super admin activo."""
    # Import diferido: users no debe cargarse al importar accounts
    from app.modules.users.infrastructure import SqlAlchemyUserRepository

    def resolve() -> int | None:
        super_admin_role = int(settings.AUTH_SUPER_ADMIN_ROLE_ID)
        for user in SqlAlchemyUserRepository(session).list_all():
            if int(user.role_id) == super_admin_role and user.is_active():
                return int(user.id)
        return None

    return resolve


def build_platform_wallet_ensurer(session: Session) -> EnsurePlatformWalletService:
    return EnsurePlatformWalletService(
        wallet_repo=SqlAlchemyPlatformWalletRepository(session),
        account_repo=SqlAlchemyAccountRepository(session),
        exchange_repo=SqlAlchemyExchangeRepository(session),
        owner_resolver=_first_super_admin_id(session),
        base_asset=settings.WALLET_BASE_ASSET,
    )


class AccountServiceFactory:
    """
    Factory para los servicios de la billetera de la plataforma.

    Uso en routes:
        factory = AccountServiceFactory(session=db)
        result = factory.get_wallet().get()
    """

    def __init__(self, session: Session):
        self._session = session

        # Repositorios del módulo
        self._account_repo = SqlAlchemyAccountRepository(session)
        self._balance_repo = SqlAlchemyAccountBalanceRepository(session)
        self._wallet_repo = SqlAlchemyPlatformWalletRepository(session)
        self._snapshot_repo = SqlAlchemyWalletSnapshotRepository(session)

        # Repositorio externo (market): exchange de la plataforma y cliente ccxt
        self._exchange_repo = SqlAlchemyExchangeRepository(session)

    # ------------------------------------------------------------------
    # Billetera de la plataforma (fondo común)
    # ------------------------------------------------------------------

    def ensure_platform_wallet(self) -> EnsurePlatformWalletService:
        return build_platform_wallet_ensurer(self._session)

    def get_wallet(self) -> GetWalletService:
        return GetWalletService(
            wallet_repo=self._wallet_repo,
            snapshot_repo=self._snapshot_repo,
            account_repo=self._account_repo,
            ensure=self.ensure_platform_wallet(),
            credentials_configured=platform_credentials_configured(),
        )

    def sync_wallet(self) -> SyncWalletService:
        return SyncWalletService(
            wallet_repo=self._wallet_repo,
            snapshot_repo=self._snapshot_repo,
            account_repo=self._account_repo,
            balance_repo=self._balance_repo,
            gateway=CcxtWalletGateway(exchange_repo=self._exchange_repo),
            ensure=self.ensure_platform_wallet(),
            credentials_configured=platform_credentials_configured(),
        )


# ======================================================================
# Dependency para FastAPI
# ======================================================================

def get_account_factory(session: Session) -> AccountServiceFactory:
    return AccountServiceFactory(session=session)
