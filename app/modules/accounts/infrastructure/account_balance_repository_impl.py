# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/account_balance_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de balances.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.modules.accounts.domain.account_balance_entity import AccountBalance
from app.modules.accounts.domain.account_balance_repository import AccountBalanceRepository
from app.modules.accounts.infrastructure.account_balance_model import AccountBalanceModel
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository


class SqlAlchemyAccountBalanceRepository(SqlAlchemyRepository, AccountBalanceRepository):
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

    def list_latest_by_account(self, account_id: int) -> list[AccountBalance]:
        # Último ts por activo (subconsulta) → una fila por activo
        latest = (
            self._session.query(
                AccountBalanceModel.asset,
                func.max(AccountBalanceModel.ts).label("max_ts"),
            )
            .filter(AccountBalanceModel.account_id == account_id)
            .group_by(AccountBalanceModel.asset)
            .subquery()
        )
        rows = (
            self._session.query(AccountBalanceModel)
            .join(
                latest,
                and_(
                    AccountBalanceModel.asset == latest.c.asset,
                    AccountBalanceModel.ts == latest.c.max_ts,
                ),
            )
            .filter(AccountBalanceModel.account_id == account_id)
            .order_by(AccountBalanceModel.asset)
            .all()
        )
        return [self._to_domain(m) for m in rows]

    def record(self, balance: AccountBalance) -> AccountBalance:
        model = AccountBalanceModel(
            account_id=balance.account_id,
            asset=balance.asset.upper(),
            free=balance.free,
            locked=balance.locked,
        )
        # La sincronización con el exchange graba todos los activos con la
        # misma hora; el registro manual deja que la ponga el servidor.
        if balance.ts is not None:
            model.ts = balance.ts
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
