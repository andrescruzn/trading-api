# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_balance_entity import AccountBalance
from app.modules.accounts.domain.account_balance_repository import AccountBalanceRepository
from app.modules.accounts.domain.account_repository import AccountRepository


class ListBalancesService:
    """
    Lista los balances de una cuenta, con filtro opcional por activo.

    Valida que la cuenta exista y que el solicitante tenga permiso.
    """

    def __init__(
        self,
        account_repo: AccountRepository,
        balance_repo: AccountBalanceRepository,
    ):
        self._account_repo = account_repo
        self._balance_repo = balance_repo

    def list(
        self,
        account_id: int,
        requester_user_id: int,
        is_admin: bool = False,
        asset: Optional[str] = None,
        limit: int = 100,
    ) -> ServiceResult[list[AccountBalance]]:
        account = self._account_repo.get_by_id(account_id)

        if account is None:
            return ServiceResult.fail(code="ACCOUNT_NOT_FOUND", http_status=404)

        if not is_admin and not account.belongs_to(requester_user_id):
            return ServiceResult.fail(code="ACCOUNT_FORBIDDEN", http_status=403)

        balances = self._balance_repo.list_by_account(
            account_id=account_id,
            asset=asset,
            limit=limit,
        )
        return ServiceResult.ok(data=balances)
