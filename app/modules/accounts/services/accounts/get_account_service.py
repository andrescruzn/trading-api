# -*- coding: utf-8 -*-

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.account_repository import AccountRepository


class GetAccountService:
    """
    Obtiene una cuenta por ID.
    Valida que el solicitante sea el dueño o un admin.
    """

    def __init__(self, repo: AccountRepository):
        self._repo = repo

    def get(
        self,
        account_id: int,
        requester_user_id: int,
        is_admin: bool = False,
    ) -> ServiceResult[Account]:
        account = self._repo.get_by_id(account_id)

        if account is None:
            return ServiceResult.fail(code="ACCOUNT_NOT_FOUND", http_status=404)

        # Solo el dueño o un admin puede ver la cuenta
        if not is_admin and not account.belongs_to(requester_user_id):
            return ServiceResult.fail(code="ACCOUNT_FORBIDDEN", http_status=403)

        return ServiceResult.ok(data=account)
