# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/domain/platform_wallet_repository.py
#
# Contratos de los repositorios de la billetera de la plataforma y de sus
# fotos de saldo. Implementados en infrastructure/.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod

from app.common.contracts import TransactionalRepository
from app.modules.accounts.domain.platform_wallet_entity import PlatformWallet
from app.modules.accounts.domain.wallet_snapshot_entity import WalletSnapshot


class PlatformWalletRepository(TransactionalRepository, ABC):

    @abstractmethod
    def get(self) -> PlatformWallet | None:
        """La billetera configurada, o None si aún no hay."""
        ...

    @abstractmethod
    def save(self, wallet: PlatformWallet) -> PlatformWallet:
        """Crea o reemplaza la única fila (sin commit)."""
        ...


class WalletSnapshotRepository(TransactionalRepository, ABC):

    @abstractmethod
    def record(self, snapshot: WalletSnapshot) -> WalletSnapshot: ...

    @abstractmethod
    def get_latest(self, account_id: int) -> WalletSnapshot | None: ...

    @abstractmethod
    def list_by_account(self, account_id: int, limit: int = 50) -> list[WalletSnapshot]:
        """Del más reciente al más antiguo."""
        ...
