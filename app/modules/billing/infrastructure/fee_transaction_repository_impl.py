# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/fee_transaction_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de FeeTransaction.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.billing.domain.fee_transaction_entity import FeeTransaction
from app.modules.billing.infrastructure.fee_transaction_model import FeeTransactionModel


class SqlAlchemyFeeTransactionRepository:
    """Repositorio de transacciones de fee con SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _to_entity(self, model: FeeTransactionModel) -> FeeTransaction:
        return FeeTransaction(
            id=model.id,
            billing_period_id=model.billing_period_id,
            managed_account_id=model.managed_account_id,
            amount=Decimal(str(model.amount)),
            status=model.status,
            charged_at=model.charged_at,
            notes=model.notes,
            created_at=model.created_at,
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def find_by_id(self, fee_tx_id: int) -> FeeTransaction | None:
        model = self._session.get(FeeTransactionModel, fee_tx_id)
        return self._to_entity(model) if model else None

    def find_by_period(self, billing_period_id: int) -> FeeTransaction | None:
        model = (
            self._session.query(FeeTransactionModel)
            .filter(FeeTransactionModel.billing_period_id == billing_period_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def list_by_managed_account(
        self, managed_account_id: int, limit: int = 50
    ) -> list[FeeTransaction]:
        models = (
            self._session.query(FeeTransactionModel)
            .filter(FeeTransactionModel.managed_account_id == managed_account_id)
            .order_by(FeeTransactionModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_entity(m) for m in models]

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def save(self, fee_tx: FeeTransaction) -> FeeTransaction:
        model = FeeTransactionModel(
            billing_period_id=fee_tx.billing_period_id,
            managed_account_id=fee_tx.managed_account_id,
            amount=str(fee_tx.amount),
            status=fee_tx.status,
            notes=fee_tx.notes,
        )
        self._session.add(model)
        self._session.flush()
        fee_tx.id = model.id
        fee_tx.created_at = model.created_at
        return fee_tx

    def update(self, fee_tx: FeeTransaction) -> FeeTransaction:
        model = self._session.get(FeeTransactionModel, fee_tx.id)
        if model:
            model.status = fee_tx.status
            model.charged_at = fee_tx.charged_at
            model.notes = fee_tx.notes
            self._session.flush()
        return fee_tx
