# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/wallet_context.py
#
# PROPÓSITO:
# - Resolver la billetera de la plataforma (M4) para los casos de uso del
#   fondo: qué cuenta es, si es live (se verifica contra el exchange) o
#   paper (desarrollo: todo se confirma a mano) y en qué moneda se lleva.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.accounts.domain.platform_wallet_repository import PlatformWalletRepository


@dataclass(frozen=True)
class WalletContext:
    account: Account
    asset: str

    @property
    def is_live(self) -> bool:
        return self.account.mode == "live"


class WalletContextResolver:
    """Billetera configurada y activa, o el código de error para el servicio."""

    def __init__(self, wallet_repo: PlatformWalletRepository, account_repo: AccountRepository):
        self._wallet_repo = wallet_repo
        self._account_repo = account_repo

    def resolve(self) -> tuple[WalletContext | None, str | None]:
        wallet = self._wallet_repo.get()
        if wallet is None:
            return None, "FUND_WALLET_NOT_CONFIGURED"
        account = self._account_repo.get_by_id(wallet.account_id)
        if account is None or not account.is_active():
            return None, "FUND_WALLET_UNAVAILABLE"
        return WalletContext(account=account, asset=wallet.base_asset.upper()), None
