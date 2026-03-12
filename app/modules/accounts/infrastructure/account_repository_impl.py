# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/account_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de cuentas.
# ======================================================================

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.accounts.infrastructure.account_model import AccountModel


class SqlAlchemyAccountRepository(AccountRepository):
    """Repositorio concreto de cuentas usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ==================================================================
    # Mappers
    # ==================================================================

    @staticmethod
    def _to_domain(model: AccountModel) -> Account:
        return Account(
            id=model.id,
            user_id=model.user_id,
            exchange_id=model.exchange_id,
            name=model.name,
            mode=model.mode,
            base_currency=model.base_currency,
            status=model.status,
            credentials_ref=model.credentials_ref,
            meta=model.meta or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _apply_domain_to_model(account: Account, model: AccountModel) -> AccountModel:
        model.user_id = account.user_id
        model.exchange_id = account.exchange_id
        model.name = account.name
        model.mode = account.mode
        model.base_currency = account.base_currency
        model.status = account.status
        model.credentials_ref = account.credentials_ref
        model.meta = account.meta
        return model

    # ==================================================================
    # Contract
    # ==================================================================

    def get_by_id(self, account_id: int) -> Optional[Account]:
        model: Optional[AccountModel] = self._session.get(AccountModel, account_id)
        return None if model is None else self._to_domain(model)

    def list_by_user_id(self, user_id: int) -> list[Account]:
        models = (
            self._session.query(AccountModel)
            .filter(AccountModel.user_id == user_id)
            .order_by(AccountModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_all(self) -> list[Account]:
        models = (
            self._session.query(AccountModel)
            .order_by(AccountModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, account: Account) -> Account:
        model = AccountModel()
        self._apply_domain_to_model(account, model)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)

    def update(self, account: Account) -> Account:
        model: Optional[AccountModel] = self._session.get(AccountModel, account.id)
        if model is None:
            raise ValueError(f"Account not found for update: id={account.id}")
        self._apply_domain_to_model(account, model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
