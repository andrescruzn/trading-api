# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/domain/account_balance_repository.py
#
# Contrato (interfaz) del repositorio de balances.
# Implementado en infrastructure/account_balance_repository_impl.py
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from app.modules.accounts.domain.account_balance_entity import AccountBalance


class AccountBalanceRepository(ABC):

    @abstractmethod
    def list_by_account(
        self,
        account_id: int,
        asset: Optional[str] = None,
        limit: int = 100,
    ) -> list[AccountBalance]: ...

    @abstractmethod
    def get_latest_by_asset(
        self,
        account_id: int,
        asset: str,
    ) -> Optional[AccountBalance]: ...

    @abstractmethod
    def record(self, balance: AccountBalance) -> AccountBalance: ...
