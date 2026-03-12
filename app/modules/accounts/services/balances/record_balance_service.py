# -*- coding: utf-8 -*-

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_balance_entity import AccountBalance
from app.modules.accounts.domain.account_balance_repository import AccountBalanceRepository
from app.modules.accounts.domain.account_repository import AccountRepository


class RecordBalanceService:
    """
    Registra un snapshot de balance para un activo en una cuenta.

    Cada llamada inserta un nuevo registro con timestamp actual,
    permitiendo trazar la evolución del balance a lo largo del tiempo
    (curva de equity por activo).

    Reglas de negocio:
    - free >= 0 y locked >= 0.
    - El activo se normaliza a mayúsculas (USDT, BTC, ETH...).
    - Solo el dueño o un admin puede registrar balances.
    """

    def __init__(
        self,
        account_repo: AccountRepository,
        balance_repo: AccountBalanceRepository,
        session: Session,
    ):
        self._account_repo = account_repo
        self._balance_repo = balance_repo
        self._session = session

    def record(
        self,
        account_id: int,
        requester_user_id: int,
        asset: str,
        free: Decimal,
        locked: Decimal,
        is_admin: bool = False,
    ) -> ServiceResult[AccountBalance]:
        # Validar cuenta y permisos
        account = self._account_repo.get_by_id(account_id)

        if account is None:
            return ServiceResult.fail(code="ACCOUNT_NOT_FOUND", http_status=404)

        if not is_admin and not account.belongs_to(requester_user_id):
            return ServiceResult.fail(code="ACCOUNT_FORBIDDEN", http_status=403)

        # Validar montos
        if free < Decimal("0") or locked < Decimal("0"):
            return ServiceResult.fail(code="BALANCE_NEGATIVE_AMOUNT", http_status=422)

        balance = AccountBalance(
            id=0,
            account_id=account_id,
            asset=asset,
            free=free,
            locked=locked,
        )

        recorded = self._balance_repo.record(balance)
        self._session.commit()
        return ServiceResult.ok(data=recorded)
