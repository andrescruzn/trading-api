# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/investors/list_investors_service.py
# ======================================================================

from __future__ import annotations

from app.common.contracts.service_result import ServiceResult
from app.modules.billing.domain.investor_entity import Investor
from app.modules.billing.domain.investor_repository import InvestorRepository


class ListInvestorsService:
    """Lista todos los inversores. Solo accesible por admin."""

    def __init__(self, repo: InvestorRepository):
        self._repo = repo

    def execute(self, only_active: bool = False) -> ServiceResult[list[Investor]]:
        investors = self._repo.list_all(only_active=only_active)
        return ServiceResult.ok(data=investors)
