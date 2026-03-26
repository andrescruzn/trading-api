# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/domain/billing_period_repository.py
#
# Contrato (Protocol) para el repositorio de BillingPeriod.
# ======================================================================

from __future__ import annotations

from typing import Protocol

from app.modules.billing.domain.billing_period_entity import BillingPeriod


class BillingPeriodRepository(Protocol):
    """Contrato para el repositorio de períodos de facturación."""

    def find_by_id(self, period_id: int) -> BillingPeriod | None: ...

    def find_open_by_managed_account(
        self, managed_account_id: int
    ) -> BillingPeriod | None: ...

    def list_by_managed_account(
        self, managed_account_id: int, limit: int = 50
    ) -> list[BillingPeriod]: ...

    def save(self, period: BillingPeriod) -> BillingPeriod: ...

    def update(self, period: BillingPeriod) -> BillingPeriod: ...
