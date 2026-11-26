# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/services/wallet/get_wallet_service.py
#
# CASOS DE USO (solo staff: super admin y socio):
# - Ver la billetera de Binance de la plataforma: su última foto de saldo,
#   cómo salió la última sincronización y si el servidor tiene sus
#   credenciales.
# - Ver la historia de fotos de saldo.
#
# NOTA:
# - Nadie elige la billetera: se asegura aquí (EnsurePlatformWalletService).
#   Sin credenciales en el `.env` no es un error: la página lo explica
#   (`credentials_configured = False`).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.accounts.domain.platform_wallet_entity import PlatformWallet
from app.modules.accounts.domain.platform_wallet_repository import (
    PlatformWalletRepository,
    WalletSnapshotRepository,
)
from app.modules.accounts.domain.wallet_snapshot_entity import WalletSnapshot
from app.modules.accounts.services.wallet.ensure_platform_wallet_service import (
    EnsurePlatformWalletService,
)


@dataclass(frozen=True)
class WalletOverview:
    wallet: PlatformWallet | None
    account: Account | None
    latest_snapshot: WalletSnapshot | None
    credentials_configured: bool


class GetWalletService:

    def __init__(
        self,
        *,
        wallet_repo: PlatformWalletRepository,
        snapshot_repo: WalletSnapshotRepository,
        account_repo: AccountRepository,
        ensure: EnsurePlatformWalletService,
        credentials_configured: bool,
    ):
        self._wallet_repo = wallet_repo
        self._snapshot_repo = snapshot_repo
        self._account_repo = account_repo
        self._ensure = ensure
        self._credentials_configured = credentials_configured

    def get(self) -> ServiceResult[WalletOverview]:
        self._ensure.ensure()
        wallet = self._wallet_repo.get()
        if wallet is None:
            return ServiceResult.ok(
                WalletOverview(None, None, None, self._credentials_configured)
            )
        return ServiceResult.ok(
            WalletOverview(
                wallet=wallet,
                account=self._account_repo.get_by_id(wallet.account_id),
                latest_snapshot=self._snapshot_repo.get_latest(wallet.account_id),
                credentials_configured=self._credentials_configured,
            )
        )

    def list_snapshots(self, limit: int = 50) -> ServiceResult[list[WalletSnapshot]]:
        wallet = self._wallet_repo.get()
        if wallet is None:
            return ServiceResult.ok([])
        return ServiceResult.ok(self._snapshot_repo.list_by_account(wallet.account_id, limit))
