# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/infrastructure/funding_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de pagos de funding.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.utils.datetime_utils import ensure_aware_utc
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository
from app.modules.orders.domain.funding_entity import FundingPayment
from app.modules.orders.domain.funding_repository import FundingRepository
from app.modules.orders.infrastructure.funding_payment_model import FundingPaymentModel


class SqlAlchemyFundingRepository(SqlAlchemyRepository, FundingRepository):

    def __init__(self, session: Session):
        self._session = session

    def latest_ts(self, bot_id: int) -> datetime | None:
        value = (
            self._session.query(func.max(FundingPaymentModel.ts))
            .filter(FundingPaymentModel.bot_id == bot_id)
            .scalar()
        )
        return ensure_aware_utc(value)

    def add_new(self, payments: list[FundingPayment]) -> int:
        if not payments:
            return 0
        account_ids = {p.account_id for p in payments}
        existing = {
            (account_id, exchange_id)
            for account_id, exchange_id in self._session.query(
                FundingPaymentModel.account_id, FundingPaymentModel.exchange_funding_id
            ).filter(
                FundingPaymentModel.account_id.in_(account_ids),
                FundingPaymentModel.exchange_funding_id.in_([p.exchange_funding_id for p in payments]),
            )
        }
        added = 0
        for payment in payments:
            key = (payment.account_id, payment.exchange_funding_id)
            if key in existing:
                continue
            existing.add(key)
            self._session.add(
                FundingPaymentModel(
                    bot_id=payment.bot_id,
                    account_id=payment.account_id,
                    symbol_id=payment.symbol_id,
                    amount=payment.amount,
                    asset=payment.asset,
                    exchange_funding_id=payment.exchange_funding_id,
                    ts=payment.ts,
                )
            )
            added += 1
        self._session.flush()
        return added

    def total_after(self, bot_id: int, after_id: int) -> tuple[Decimal, int]:
        total, last_id = (
            self._session.query(
                func.coalesce(func.sum(FundingPaymentModel.amount), 0),
                func.max(FundingPaymentModel.id),
            )
            .filter(FundingPaymentModel.bot_id == bot_id, FundingPaymentModel.id > after_id)
            .one()
        )
        return Decimal(str(total)), int(last_id or after_id)

    def total_by_bot(self, bot_id: int) -> Decimal:
        total = (
            self._session.query(func.coalesce(func.sum(FundingPaymentModel.amount), 0))
            .filter(FundingPaymentModel.bot_id == bot_id)
            .scalar()
        )
        return Decimal(str(total))
