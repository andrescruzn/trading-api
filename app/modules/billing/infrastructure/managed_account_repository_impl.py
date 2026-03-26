# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/managed_account_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de ManagedAccount.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.billing.domain.managed_account_entity import ManagedAccount
from app.modules.billing.infrastructure.managed_account_model import ManagedAccountModel


class SqlAlchemyManagedAccountRepository:
    """Repositorio de cuentas gestionadas con SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _to_entity(self, model: ManagedAccountModel) -> ManagedAccount:
        return ManagedAccount(
            id=model.id,
            investor_id=model.investor_id,
            account_id=model.account_id,
            bot_id=model.bot_id,
            name=model.name,
            initial_capital=Decimal(str(model.initial_capital)),
            high_water_mark=Decimal(str(model.high_water_mark)),
            period_type=model.period_type,
            is_active=bool(model.is_active),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def find_by_id(self, managed_account_id: int) -> ManagedAccount | None:
        model = self._session.get(ManagedAccountModel, managed_account_id)
        return self._to_entity(model) if model else None

    def list_by_investor(self, investor_id: int) -> list[ManagedAccount]:
        models = (
            self._session.query(ManagedAccountModel)
            .filter(ManagedAccountModel.investor_id == investor_id)
            .order_by(ManagedAccountModel.id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_all(self, only_active: bool = False) -> list[ManagedAccount]:
        query = self._session.query(ManagedAccountModel)
        if only_active:
            query = query.filter(ManagedAccountModel.is_active == True)  # noqa: E712
        return [self._to_entity(m) for m in query.order_by(ManagedAccountModel.id).all()]

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def save(self, managed_account: ManagedAccount) -> ManagedAccount:
        if managed_account.id == 0:
            model = ManagedAccountModel(
                investor_id=managed_account.investor_id,
                account_id=managed_account.account_id,
                bot_id=managed_account.bot_id,
                name=managed_account.name,
                initial_capital=str(managed_account.initial_capital),
                high_water_mark=str(managed_account.high_water_mark),
                period_type=managed_account.period_type,
                is_active=managed_account.is_active,
            )
            self._session.add(model)
            self._session.flush()
            managed_account.id = model.id
        else:
            model = self._session.get(ManagedAccountModel, managed_account.id)
            if model:
                model.bot_id = managed_account.bot_id
                model.name = managed_account.name
                model.period_type = managed_account.period_type
                model.is_active = managed_account.is_active
                self._session.flush()
        return managed_account

    def update_high_water_mark(
        self, managed_account_id: int, new_hwm: Decimal
    ) -> None:
        """Actualiza solo el campo high_water_mark de la cuenta gestionada."""
        model = self._session.get(ManagedAccountModel, managed_account_id)
        if model:
            model.high_water_mark = str(new_hwm)
            self._session.flush()
