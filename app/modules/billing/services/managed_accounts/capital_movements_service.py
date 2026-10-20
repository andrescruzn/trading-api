# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/managed_accounts/capital_movements_service.py
#
# CASOS DE USO:
# - Registrar un aporte o un retiro del inversor (admin).
# - Listar los movimientos de una cuenta (admin o el inversor dueño).
#
# REGLA DE NEGOCIO — no cobrar comisión sobre dinero que no es ganancia:
# - Aporte de A: la marca de agua sube A y, si hay un período abierto, su
#   equity de apertura también sube A (como si el dinero hubiera estado
#   desde el inicio). Así la comisión solo mide lo que ganó la cuenta.
# - Retiro de R: la marca de agua y la apertura del período abierto bajan
#   R (sin quedar por debajo de 0). Es un ajuste por monto, no
#   proporcional: simple y predecible, y nunca cobra sobre el retiro.
# - Todo en un commit: movimiento + marca de agua + período.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.billing.domain.billing_period_repository import BillingPeriodRepository
from app.modules.billing.domain.capital_movement_entity import CapitalMovement
from app.modules.billing.domain.capital_movement_repository import CapitalMovementRepository
from app.modules.billing.domain.managed_account_repository import ManagedAccountRepository

_ZERO = Decimal("0")


@dataclass
class CapitalSummary:
    movements: list[CapitalMovement]
    deposits: Decimal
    withdrawals: Decimal

    @property
    def net(self) -> Decimal:
        return self.deposits - self.withdrawals


class RecordCapitalMovementService:
    """Registra un aporte o retiro y ajusta la marca de agua."""

    def __init__(
        self,
        movement_repo: CapitalMovementRepository,
        managed_account_repo: ManagedAccountRepository,
        period_repo: BillingPeriodRepository,
    ):
        self._movement_repo = movement_repo
        self._managed_account_repo = managed_account_repo
        self._period_repo = period_repo

    def execute(
        self,
        managed_account_id: int,
        kind: str,
        amount: Decimal,
        ts: datetime | None = None,
        notes: str | None = None,
        created_by_user_id: int | None = None,
    ) -> ServiceResult[CapitalMovement]:
        if kind not in CapitalMovement.KINDS:
            return ServiceResult.fail(code="CAPITAL_INVALID_KIND", http_status=422)
        if amount <= _ZERO:
            return ServiceResult.fail(code="CAPITAL_INVALID_AMOUNT", http_status=422)

        account = self._managed_account_repo.find_by_id(managed_account_id)
        if account is None:
            return ServiceResult.fail(code="BILLING_MANAGED_ACCOUNT_NOT_FOUND", http_status=404)
        if not account.is_active:
            return ServiceResult.fail(code="BILLING_MANAGED_ACCOUNT_INACTIVE", http_status=409)

        movement = CapitalMovement(
            id=0,
            managed_account_id=managed_account_id,
            kind=kind,
            amount=amount,
            ts=ts or utc_now(),
            notes=notes,
            created_by_user_id=created_by_user_id,
        )
        delta = movement.signed_amount()

        try:
            movement = self._movement_repo.save(movement)
            self._managed_account_repo.update_high_water_mark(
                managed_account_id, max(account.high_water_mark + delta, _ZERO)
            )
            period = self._period_repo.find_open_by_managed_account(managed_account_id)
            if period is not None:
                period.opening_equity = max(period.opening_equity + delta, _ZERO)
                self._period_repo.update(period)
            self._movement_repo.commit()
        except Exception:
            self._movement_repo.rollback()
            raise

        return ServiceResult.ok(data=movement)


class ListCapitalMovementsService:
    """Aportes y retiros de una cuenta, con los totales."""

    def __init__(
        self,
        movement_repo: CapitalMovementRepository,
        managed_account_repo: ManagedAccountRepository,
    ):
        self._movement_repo = movement_repo
        self._managed_account_repo = managed_account_repo

    def execute(
        self, managed_account_id: int, investor_id: int | None = None
    ) -> ServiceResult[CapitalSummary]:
        account = self._managed_account_repo.find_by_id(managed_account_id)
        if account is None:
            return ServiceResult.fail(code="BILLING_MANAGED_ACCOUNT_NOT_FOUND", http_status=404)
        if investor_id is not None and account.investor_id != investor_id:
            return ServiceResult.fail(code="BILLING_MANAGED_ACCOUNT_FORBIDDEN", http_status=403)

        movements = self._movement_repo.list_by_managed_account(managed_account_id)
        deposits = sum((m.amount for m in movements if m.kind == "deposit"), _ZERO)
        withdrawals = sum((m.amount for m in movements if m.kind == "withdrawal"), _ZERO)
        return ServiceResult.ok(
            data=CapitalSummary(movements=movements, deposits=deposits, withdrawals=withdrawals)
        )
