# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/investors/update_investor_service.py
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.contracts.service_result import ServiceResult
from app.modules.billing.domain.investor_entity import Investor
from app.modules.billing.domain.investor_repository import InvestorRepository


class UpdateInvestorService:
    """Actualiza fee_pct y/o is_active de un inversor."""

    def __init__(self, repo: InvestorRepository, session: Session):
        self._repo = repo
        self._session = session

    def execute(
        self,
        investor_id: int,
        fee_pct: Decimal | None = None,
        is_active: bool | None = None,
    ) -> ServiceResult[Investor]:
        investor = self._repo.find_by_id(investor_id)
        if not investor:
            return ServiceResult.fail(
                code="BILLING_INVESTOR_NOT_FOUND",
                http_status=404,
            )

        if fee_pct is not None:
            if not (Decimal("0") <= fee_pct <= Decimal("1")):
                return ServiceResult.fail(
                    code="BILLING_INVALID_FEE_PCT",
                    http_status=422,
                )
            investor.fee_pct = fee_pct

        if is_active is not None:
            investor.is_active = is_active

        saved = self._repo.save(investor)
        self._session.commit()
        return ServiceResult.ok(data=saved)
