# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/capital_movement_repository_impl.py
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository
from app.modules.billing.domain.capital_movement_entity import CapitalMovement
from app.modules.billing.infrastructure.capital_movement_model import CapitalMovementModel


class SqlAlchemyCapitalMovementRepository(SqlAlchemyRepository):
    """Aportes y retiros con SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_entity(model: CapitalMovementModel) -> CapitalMovement:
        return CapitalMovement(
            id=model.id,
            managed_account_id=model.managed_account_id,
            kind=model.kind,
            amount=Decimal(str(model.amount)),
            ts=model.ts,
            notes=model.notes,
            created_by_user_id=model.created_by_user_id,
            created_at=model.created_at,
        )

    def list_by_managed_account(self, managed_account_id: int) -> list[CapitalMovement]:
        models = (
            self._session.query(CapitalMovementModel)
            .filter(CapitalMovementModel.managed_account_id == managed_account_id)
            .order_by(CapitalMovementModel.ts.desc(), CapitalMovementModel.id.desc())
            .all()
        )
        return [self._to_entity(m) for m in models]

    def save(self, movement: CapitalMovement) -> CapitalMovement:
        model = CapitalMovementModel(
            managed_account_id=movement.managed_account_id,
            kind=movement.kind,
            amount=movement.amount,
            ts=movement.ts,
            notes=movement.notes,
            created_by_user_id=movement.created_by_user_id,
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_entity(model)
