# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/billing/close_billing_period_service.py
#
# Cierra un período de facturación aplicando la lógica de High-Water Mark.
#
# Flujo atómico en un solo commit:
#   1. Calcular gross_pnl con HWM
#   2. Calcular fee_amount y net_pnl
#   3. Actualizar el BillingPeriod → status=closed
#   4. Si hay fee > 0: crear FeeTransaction (status=pending)
#   5. Si hay ganancia: actualizar HWM en ManagedAccount
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.contracts.service_result import ServiceResult
from app.modules.billing.domain.billing_period_entity import BillingPeriod
from app.modules.billing.domain.billing_period_repository import BillingPeriodRepository
from app.modules.billing.domain.fee_transaction_entity import FeeTransaction
from app.modules.billing.domain.fee_transaction_repository import FeeTransactionRepository
from app.modules.billing.domain.managed_account_repository import ManagedAccountRepository


class CloseBillingPeriodService:
    """
    Cierra un período de facturación aplicando High-Water Mark.

    Resultado devuelto: el BillingPeriod actualizado con todos los campos
    calculados (gross_pnl, fee_amount, net_pnl).

    La FeeTransaction creada (si aplica) queda en status=pending.
    El admin puede luego marcarla como charged o waived.
    """

    def __init__(
        self,
        period_repo: BillingPeriodRepository,
        fee_tx_repo: FeeTransactionRepository,
        managed_account_repo: ManagedAccountRepository,
        session: Session,
    ):
        self._period_repo = period_repo
        self._fee_tx_repo = fee_tx_repo
        self._managed_account_repo = managed_account_repo
        self._session = session

    def execute(
        self,
        period_id: int,
        closing_equity: Decimal,
    ) -> ServiceResult[BillingPeriod]:
        # Verificar que el período existe y está abierto
        period = self._period_repo.find_by_id(period_id)
        if not period:
            return ServiceResult.fail(
                code="BILLING_PERIOD_NOT_FOUND",
                http_status=404,
            )
        if period.is_closed():
            return ServiceResult.fail(
                code="BILLING_PERIOD_ALREADY_CLOSED",
                http_status=409,
            )

        # Obtener la cuenta para leer el HWM actual
        account = self._managed_account_repo.find_by_id(period.managed_account_id)
        if not account:
            return ServiceResult.fail(
                code="BILLING_MANAGED_ACCOUNT_NOT_FOUND",
                http_status=404,
            )

        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)

        # Aplicar cálculo HWM en la entidad (lógica de dominio pura)
        period.calculate_fee(
            closing_equity=closing_equity,
            high_water_mark=account.high_water_mark,
        )
        period.status = BillingPeriod.STATUS_CLOSED
        period.end_ts = now
        period.closed_at = now

        # Persistir el período cerrado
        self._period_repo.update(period)

        # Si hay fee a cobrar → crear FeeTransaction (status=pending)
        if period.has_fee_to_charge():
            fee_tx = FeeTransaction(
                id=0,
                billing_period_id=period.id,
                managed_account_id=account.id,
                amount=period.fee_amount,  # type: ignore[arg-type]
                status=FeeTransaction.STATUS_PENDING,
            )
            self._fee_tx_repo.save(fee_tx)

        # Actualizar HWM solo si closing_equity supera el HWM actual (nuevo máximo real).
        # No basta con gross_pnl > 0: si opening < hwm y closing está entre ambos,
        # gross_pnl sería positivo pero el HWM NO debe decrecer.
        if closing_equity > account.high_water_mark:
            self._managed_account_repo.update_high_water_mark(
                managed_account_id=account.id,
                new_hwm=closing_equity,
            )

        self._session.commit()
        return ServiceResult.ok(data=period)
