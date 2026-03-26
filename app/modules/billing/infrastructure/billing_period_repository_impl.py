# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/billing_period_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de BillingPeriod.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.billing.domain.billing_period_entity import BillingPeriod
from app.modules.billing.infrastructure.billing_period_model import BillingPeriodModel


class SqlAlchemyBillingPeriodRepository:
    """Repositorio de períodos de facturación con SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _to_entity(self, model: BillingPeriodModel) -> BillingPeriod:
        return BillingPeriod(
            id=model.id,
            managed_account_id=model.managed_account_id,
            start_ts=model.start_ts,
            end_ts=model.end_ts,
            opening_equity=Decimal(str(model.opening_equity)),
            closing_equity=Decimal(str(model.closing_equity)) if model.closing_equity is not None else None,
            gross_pnl=Decimal(str(model.gross_pnl)) if model.gross_pnl is not None else None,
            fee_pct=Decimal(str(model.fee_pct)),
            fee_amount=Decimal(str(model.fee_amount)) if model.fee_amount is not None else None,
            net_pnl=Decimal(str(model.net_pnl)) if model.net_pnl is not None else None,
            status=model.status,
            created_at=model.created_at,
            closed_at=model.closed_at,
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def find_by_id(self, period_id: int) -> BillingPeriod | None:
        model = self._session.get(BillingPeriodModel, period_id)
        return self._to_entity(model) if model else None

    def find_open_by_managed_account(
        self, managed_account_id: int
    ) -> BillingPeriod | None:
        model = (
            self._session.query(BillingPeriodModel)
            .filter(
                BillingPeriodModel.managed_account_id == managed_account_id,
                BillingPeriodModel.status == "open",
            )
            .first()
        )
        return self._to_entity(model) if model else None

    def list_by_managed_account(
        self, managed_account_id: int, limit: int = 50
    ) -> list[BillingPeriod]:
        models = (
            self._session.query(BillingPeriodModel)
            .filter(BillingPeriodModel.managed_account_id == managed_account_id)
            .order_by(BillingPeriodModel.start_ts.desc())
            .limit(limit)
            .all()
        )
        return [self._to_entity(m) for m in models]

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def save(self, period: BillingPeriod) -> BillingPeriod:
        model = BillingPeriodModel(
            managed_account_id=period.managed_account_id,
            opening_equity=str(period.opening_equity),
            fee_pct=str(period.fee_pct),
            status=period.status,
        )
        self._session.add(model)
        self._session.flush()
        period.id = model.id
        period.start_ts = model.start_ts
        period.created_at = model.created_at
        return period

    def update(self, period: BillingPeriod) -> BillingPeriod:
        model = self._session.get(BillingPeriodModel, period.id)
        if model:
            model.end_ts = period.end_ts
            model.closing_equity = str(period.closing_equity) if period.closing_equity is not None else None
            model.gross_pnl = str(period.gross_pnl) if period.gross_pnl is not None else None
            model.fee_amount = str(period.fee_amount) if period.fee_amount is not None else None
            model.net_pnl = str(period.net_pnl) if period.net_pnl is not None else None
            model.status = period.status
            model.closed_at = period.closed_at
            self._session.flush()
        return period
