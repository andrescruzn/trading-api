# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/ledger/fund_ledger_service.py
#
# CASOS DE USO:
# - balances(user_id)  → saldos de una persona (pendiente de asignar,
#                        disponible). La propia persona o el staff.
# - all_balances()     → saldos de todas las personas con movimientos (staff).
# - ledger(user_id, …) → asientos de una persona, paginados.
# - refund(...)        → devolución excepcional de saldo pendiente de asignar
#                        (super admin, con motivo). El dinero se devuelve por
#                        fuera; aquí queda el asiento que lo explica.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from app.common.contracts import Page, PageRequest, ServiceResult
from app.modules.fund.domain.fund_repositories import LedgerRepository
from app.modules.fund.domain.ledger_entry_entity import FundBalances, LedgerEntry
from app.modules.users.domain import UserRepository

MIN_REASON_LENGTH = 5
MAX_REASON_LENGTH = 500


class FundLedgerService:

    def __init__(self, *, ledger_repo: LedgerRepository, user_repo: UserRepository, asset: str):
        self._ledger_repo = ledger_repo
        self._user_repo = user_repo
        self._asset = asset.upper()

    def balances(self, user_id: int) -> ServiceResult[FundBalances]:
        return ServiceResult.ok(self._ledger_repo.balances_for(int(user_id)))

    def all_balances(self) -> ServiceResult[list[FundBalances]]:
        return ServiceResult.ok(self._ledger_repo.balances_by_user())

    def ledger(self, user_id: int, page: PageRequest) -> ServiceResult[Page[LedgerEntry]]:
        return ServiceResult.ok(self._ledger_repo.list_page(int(user_id), page))

    def refund(
        self,
        *,
        user_id: int,
        amount: Decimal,
        reason: str | None,
        requester_user_id: int,
    ) -> ServiceResult[LedgerEntry]:
        clean_reason = (reason or "").strip()
        if not MIN_REASON_LENGTH <= len(clean_reason) <= MAX_REASON_LENGTH:
            return ServiceResult.fail(code="FUND_REFUND_REASON_REQUIRED", http_status=422)
        if amount <= 0:
            return ServiceResult.fail(code="FUND_REFUND_INVALID_AMOUNT", http_status=422)
        if self._user_repo.get_by_id(int(user_id)) is None:
            return ServiceResult.fail(code="FUND_USER_NOT_FOUND", http_status=404)

        # Solo se devuelve lo que aún no pasó por un agente
        if amount > self._ledger_repo.balances_for(int(user_id)).pending:
            return ServiceResult.fail(code="FUND_REFUND_EXCEEDS_PENDING", http_status=409)

        try:
            entry = self._ledger_repo.add(
                LedgerEntry(
                    id=0,
                    user_id=int(user_id),
                    entry_type="refund",
                    bucket="pending",
                    amount=-amount,
                    asset=self._asset,
                    description=clean_reason,
                    created_by_user_id=int(requester_user_id),
                )
            )
            self._ledger_repo.commit()
        except Exception:
            self._ledger_repo.rollback()
            raise
        return ServiceResult.ok(entry)
