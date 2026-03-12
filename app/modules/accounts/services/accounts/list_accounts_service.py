# -*- coding: utf-8 -*-

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.account_repository import AccountRepository


class ListAccountsService:
    """
    Lista las cuentas de un usuario.
    Los admins pueden listar todas las cuentas del sistema.
    """

    def __init__(self, repo: AccountRepository):
        self._repo = repo

    def list(
        self,
        user_id: int,
        is_admin: bool = False,
    ) -> ServiceResult[list[Account]]:
        if is_admin:
            accounts = self._repo.list_all()
        else:
            accounts = self._repo.list_by_user_id(user_id)
        return ServiceResult.ok(data=accounts)
