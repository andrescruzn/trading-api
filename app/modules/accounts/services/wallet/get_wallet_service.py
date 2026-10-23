# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/services/wallet/get_wallet_service.py
#
# CASOS DE USO (solo staff: super admin y socio):
# - Ver la billetera de la plataforma: qué cuenta es, su última foto de
#   saldo y cómo salió la última sincronización.
# - Ver la historia de fotos de saldo.
#
# NOTA:
# - Sin billetera configurada no es un error: la página explica cómo
#   elegirla (`wallet = None`).
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


@dataclass(frozen=True)
class WalletOverview:
    wallet: PlatformWallet | None
    account: Account | None
    latest_snapshot: WalletSnapshot | None


class GetWalletService:

    def __init__(
        self,
        *,
        wallet_repo: PlatformWalletRepository,
        snapshot_repo: WalletSnapshotRepository,
        account_repo: AccountRepository,
    ):
        self._wallet_repo = wallet_repo
        self._snapshot_repo = snapshot_repo
        self._account_repo = account_repo

    def get(self) -> ServiceResult[WalletOverview]:
        wallet = self._wallet_repo.get()
        if wallet is None:
            return ServiceResult.ok(WalletOverview(None, None, None))
        return ServiceResult.ok(
            WalletOverview(
                wallet=wallet,
                account=self._account_repo.get_by_id(wallet.account_id),
                latest_snapshot=self._snapshot_repo.get_latest(wallet.account_id),
            )
        )

    def list_snapshots(self, limit: int = 50) -> ServiceResult[list[WalletSnapshot]]:
        wallet = self._wallet_repo.get()
        if wallet is None:
            return ServiceResult.ok([])
        return ServiceResult.ok(self._snapshot_repo.list_by_account(wallet.account_id, limit))
