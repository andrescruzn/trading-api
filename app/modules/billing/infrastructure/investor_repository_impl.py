# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/investor_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de Investor.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.billing.domain.investor_entity import Investor
from app.modules.billing.infrastructure.investor_model import InvestorModel


class SqlAlchemyInvestorRepository:
    """Repositorio de inversores con SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _to_entity(self, model: InvestorModel) -> Investor:
        return Investor(
            id=model.id,
            user_id=model.user_id,
            fee_pct=Decimal(str(model.fee_pct)),
            is_active=bool(model.is_active),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def find_by_id(self, investor_id: int) -> Investor | None:
        model = self._session.get(InvestorModel, investor_id)
        return self._to_entity(model) if model else None

    def find_by_user_id(self, user_id: int) -> Investor | None:
        model = (
            self._session.query(InvestorModel)
            .filter(InvestorModel.user_id == user_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def list_all(self, only_active: bool = False) -> list[Investor]:
        query = self._session.query(InvestorModel)
        if only_active:
            query = query.filter(InvestorModel.is_active == True)  # noqa: E712
        return [self._to_entity(m) for m in query.order_by(InvestorModel.id).all()]

    # ------------------------------------------------------------------
    # Writes — commit() se hace en el llamador (service)
    # ------------------------------------------------------------------

    def save(self, investor: Investor) -> Investor:
        if investor.id == 0:
            # Nuevo registro
            model = InvestorModel(
                user_id=investor.user_id,
                fee_pct=str(investor.fee_pct),
                is_active=investor.is_active,
            )
            self._session.add(model)
            self._session.flush()
            investor.id = model.id
        else:
            # Actualización
            model = self._session.get(InvestorModel, investor.id)
            if model:
                model.fee_pct = str(investor.fee_pct)
                model.is_active = investor.is_active
                self._session.flush()
        return investor
