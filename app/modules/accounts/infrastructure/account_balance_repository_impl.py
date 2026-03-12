# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/account_balance_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de balances.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.accounts.domain.account_balance_entity import AccountBalance
from app.modules.accounts.domain.account_balance_repository import AccountBalanceRepository
from app.modules.accounts.infrastructure.account_balance_model import AccountBalanceModel


class SqlAlchemyAccountBalanceRepository(AccountBalanceRepository):
    """Repositorio concreto de balances de cuenta usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ==================================================================
    # Mappers
    # ==================================================================

    @staticmethod
    def _to_domain(model: AccountBalanceModel) -> AccountBalance:
        return AccountBalance(
            id=model.id,
            account_id=model.account_id,
            asset=model.asset,
            free=Decimal(str(model.free)),
            locked=Decimal(str(model.locked)),
            ts=model.ts,
        )

    # ==================================================================
    # Contract
    # ==================================================================

    def list_by_account(
        self,
        account_id: int,
        asset: Optional[str] = None,
        limit: int = 100,
    ) -> list[AccountBalance]:
        query = (
            self._session.query(AccountBalanceModel)
            .filter(AccountBalanceModel.account_id == account_id)
        )
        if asset:
            query = query.filter(AccountBalanceModel.asset == asset.upper())
        query = query.order_by(AccountBalanceModel.ts.desc()).limit(limit)
        return [self._to_domain(m) for m in query.all()]

    def get_latest_by_asset(self, account_id: int, asset: str) -> Optional[AccountBalance]:
        model = (
            self._session.query(AccountBalanceModel)
            .filter(
                AccountBalanceModel.account_id == account_id,
                AccountBalanceModel.asset == asset.upper(),
            )
            .order_by(AccountBalanceModel.ts.desc())
            .first()
        )
        return None if model is None else self._to_domain(model)

    def record(self, balance: AccountBalance) -> AccountBalance:
        model = AccountBalanceModel(
            account_id=balance.account_id,
            asset=balance.asset.upper(),
            free=balance.free,
            locked=balance.locked,
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
