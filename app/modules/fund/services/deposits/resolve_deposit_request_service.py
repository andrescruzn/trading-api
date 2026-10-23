# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/deposits/resolve_deposit_request_service.py
#
# CASOS DE USO:
# - list(...)    → solicitudes paginadas (cada quien las suyas; el staff, todas).
# - cancel(...)  → el participante anula su solicitud mientras está `pending`.
# - confirm(...) → un super admin la confirma (pending o review).
# - reject(...)  → un super admin la rechaza (pending o review), con motivo.
#
# REGLAS:
# - Confirmar a mano exige nota si el monto no es el que reportó el
#   exchange (o si el exchange no lo reportó): queda escrito por qué.
# - Rechazar exige motivo: la persona lo ve en su historial.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from app.common.contracts import Page, PageRequest, ServiceResult
from app.common.utils import utc_now
from app.modules.fund.domain.deposit_request_entity import (
    DEPOSIT_STATUSES,
    OPEN_DEPOSIT_STATUSES,
    DepositRequest,
)
from app.modules.fund.domain.fund_repositories import DepositRequestRepository, LedgerRepository
from app.modules.fund.services.deposits.deposit_crediting import DepositCreditor

MAX_NOTE_LENGTH = 500


def _clean_note(note: str | None) -> str | None:
    text = (note or "").strip()
    return text[:MAX_NOTE_LENGTH] or None


class ResolveDepositRequestService:

    def __init__(self, *, deposit_repo: DepositRequestRepository, ledger_repo: LedgerRepository):
        self._deposit_repo = deposit_repo
        self._creditor = DepositCreditor(deposit_repo, ledger_repo)

    # ------------------------------------------------------------------
    # Listado
    # ------------------------------------------------------------------

    def list(
        self,
        *,
        page: PageRequest,
        owner_id: int | None,
        status: str | None = None,
    ) -> ServiceResult[Page[DepositRequest]]:
        """`owner_id` None = todas (staff); si no, solo las de esa persona."""
        if status is not None and status not in DEPOSIT_STATUSES:
            return ServiceResult.fail(code="FUND_DEPOSIT_INVALID_STATUS", http_status=422)
        return ServiceResult.ok(
            self._deposit_repo.list_page(
                page, user_id=owner_id, statuses=[status] if status else None
            )
        )

    # ------------------------------------------------------------------
    # Participante
    # ------------------------------------------------------------------

    def cancel(self, request_id: int, user_id: int) -> ServiceResult[DepositRequest]:
        request = self._deposit_repo.get_by_id(request_id)
        if request is None or not request.belongs_to(user_id):
            return ServiceResult.fail(code="FUND_DEPOSIT_NOT_FOUND", http_status=404)
        if request.status != "pending":
            return ServiceResult.fail(code="FUND_DEPOSIT_NOT_CANCELABLE", http_status=409)

        request.status = "canceled"
        request.resolved_at = utc_now()
        try:
            if not self._deposit_repo.update_if_status(request, ["pending"]):
                self._deposit_repo.rollback()
                return ServiceResult.fail(code="FUND_DEPOSIT_NOT_CANCELABLE", http_status=409)
            self._deposit_repo.commit()
        except Exception:
            self._deposit_repo.rollback()
            raise
        return ServiceResult.ok(request)

    # ------------------------------------------------------------------
    # Super admin
    # ------------------------------------------------------------------

    def confirm(
        self,
        request_id: int,
        *,
        requester_user_id: int,
        amount: Decimal | None = None,
        note: str | None = None,
    ) -> ServiceResult[DepositRequest]:
        request = self._deposit_repo.get_by_id(request_id)
        if request is None:
            return ServiceResult.fail(code="FUND_DEPOSIT_NOT_FOUND", http_status=404)
        if not request.is_open():
            return ServiceResult.fail(code="FUND_DEPOSIT_ALREADY_RESOLVED", http_status=409)

        to_credit = amount if amount is not None else request.amount_to_credit()
        if to_credit <= 0:
            return ServiceResult.fail(code="FUND_DEPOSIT_INVALID_AMOUNT", http_status=422)

        clean_note = _clean_note(note)
        # Sin respaldo del exchange (o con otro monto) la decisión queda escrita
        if clean_note is None and (
            request.credited_amount is None or to_credit != request.credited_amount
        ):
            return ServiceResult.fail(code="FUND_DEPOSIT_NOTE_REQUIRED", http_status=422)

        try:
            confirmed = self._creditor.confirm(
                request,
                amount=to_credit,
                now=utc_now(),
                expected=list(OPEN_DEPOSIT_STATUSES),
                resolved_by_user_id=int(requester_user_id),
                note=clean_note,
            )
            if not confirmed:
                self._deposit_repo.rollback()
                return ServiceResult.fail(code="FUND_DEPOSIT_ALREADY_RESOLVED", http_status=409)
            self._deposit_repo.commit()
        except Exception:
            self._deposit_repo.rollback()
            raise
        return ServiceResult.ok(request)

    def reject(
        self, request_id: int, *, requester_user_id: int, note: str | None
    ) -> ServiceResult[DepositRequest]:
        request = self._deposit_repo.get_by_id(request_id)
        if request is None:
            return ServiceResult.fail(code="FUND_DEPOSIT_NOT_FOUND", http_status=404)
        if not request.is_open():
            return ServiceResult.fail(code="FUND_DEPOSIT_ALREADY_RESOLVED", http_status=409)
        clean_note = _clean_note(note)
        if clean_note is None:
            return ServiceResult.fail(code="FUND_DEPOSIT_NOTE_REQUIRED", http_status=422)

        request.status = "rejected"
        request.resolved_at = utc_now()
        request.resolved_by_user_id = int(requester_user_id)
        request.resolution_note = clean_note
        try:
            if not self._deposit_repo.update_if_status(request, list(OPEN_DEPOSIT_STATUSES)):
                self._deposit_repo.rollback()
                return ServiceResult.fail(code="FUND_DEPOSIT_ALREADY_RESOLVED", http_status=409)
            self._deposit_repo.commit()
        except Exception:
            self._deposit_repo.rollback()
            raise
        return ServiceResult.ok(request)
