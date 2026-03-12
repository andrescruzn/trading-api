# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/domain/account_repository.py
#
# Contrato (interfaz) del repositorio de cuentas.
# Implementado en infrastructure/account_repository_impl.py
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.accounts.domain.account_entity import Account


class AccountRepository(ABC):

    @abstractmethod
    def get_by_id(self, account_id: int) -> Optional[Account]: ...

    @abstractmethod
    def list_by_user_id(self, user_id: int) -> list[Account]: ...

    @abstractmethod
    def list_all(self) -> list[Account]: ...

    @abstractmethod
    def create(self, account: Account) -> Account: ...

    @abstractmethod
    def update(self, account: Account) -> Account: ...
