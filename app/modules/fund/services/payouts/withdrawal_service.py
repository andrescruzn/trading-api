# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/payouts/withdrawal_service.py
#
# CASOS DE USO:
# - free_available(user_id) → lo que la persona puede retirar o reinvertir:
#                             disponible − retiros sin pagar − asignaciones en
#                             cola desde el disponible.
# - create(...)             → pedir un retiro a banco / Nequi.
# - cancel(...)             → anularlo mientras no se haya pagado.
# - list(...)               → los propios; el staff ve todos.
# - mark_paid(...)          → un super admin lo pagó por fuera: COP, tasa y
#                             referencia; sale del saldo (asiento `withdrawal`).
# - reject(...)             → un super admin lo rechaza con motivo.
# - attach_receipt(...)     → un super admin sube (o cambia) el comprobante de
#                             un retiro pagado (F6).
# - get_receipt(...)        → el comprobante, para la persona o el staff.
#
# REGLAS:
# - Solo se retira el saldo disponible: lo que ya pasó por un agente (o
#   comisiones). Lo pendiente de asignar no se retira.
# - El medio de pago debe ser de la persona, estar activo y haber cumplido
#   su espera de seguridad.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from app.common.contracts import Page, PageRequest, ServiceResult
from app.common.utils import utc_now
from app.modules.fund.domain.fund_notifier import (
    FUND_WITHDRAWAL_PAID,
    FUND_WITHDRAWAL_REJECTED,
    FUND_WITHDRAWAL_REQUESTED,
    FundEvent,
    FundNotifier,
    NullFundNotifier,
)
from app.modules.fund.domain.fund_repositories import AllocationOrderRepository, LedgerRepository
from app.modules.fund.domain.ledger_entry_entity import LedgerEntry
from app.modules.fund.domain.payout_repositories import (
    PayoutMethodRepository,
    WithdrawalReceiptRepository,
    WithdrawalRequestRepository,
)
from app.modules.fund.domain.withdrawal_entity import (
    MAX_RECEIPT_BYTES,
    WITHDRAWAL_STATUSES,
    WithdrawalReceipt,
    WithdrawalRequest,
    clean_receipt_name,
    decode_receipt,
    detect_receipt_type,
)

WITHDRAWAL_REF_TYPE = "withdrawal_request"
MAX_OPEN_WITHDRAWALS = 5
MAX_NOTE_LENGTH = 500


class WithdrawalService:

    def __init__(
        self,
        *,
        repo: WithdrawalRequestRepository,
        payout_repo: PayoutMethodRepository,
        ledger_repo: LedgerRepository,
        allocation_repo: AllocationOrderRepository,
        receipt_repo: WithdrawalReceiptRepository,
        asset: str,
        notifier: FundNotifier | None = None,
    ):
        self._notifier = notifier or NullFundNotifier()
        self._receipt_repo = receipt_repo
        self._repo = repo
        self._payout_repo = payout_repo
        self._ledger_repo = ledger_repo
        self._allocation_repo = allocation_repo
        self._asset = asset.upper()

    # ------------------------------------------------------------------
    # Participante
    # ------------------------------------------------------------------

    def free_available(self, user_id: int) -> Decimal:
        available = self._ledger_repo.bucket_balance(int(user_id), "available")
        return (
            available
            - self._repo.open_total(int(user_id))
            - self._allocation_repo.queued_total(int(user_id), "available")
        )

    def create(
        self, *, user_id: int, amount: Decimal, payout_method_id: int
    ) -> ServiceResult[WithdrawalRequest]:
        if amount <= 0:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_INVALID_AMOUNT", http_status=422)
        method = self._payout_repo.get_by_id(int(payout_method_id))
        if method is None or not method.belongs_to(user_id) or not method.is_active:
            return ServiceResult.fail(code="FUND_PAYOUT_NOT_FOUND", http_status=404)
        if not method.is_usable(utc_now()):
            return ServiceResult.fail(
                code="FUND_PAYOUT_COOLING_DOWN",
                http_status=409,
                meta={"usable_from": method.usable_from.isoformat()},
            )
        free = self.free_available(user_id)
        if amount > free:
            return ServiceResult.fail(
                code="FUND_WITHDRAWAL_EXCEEDS_AVAILABLE",
                http_status=409,
                meta={"free": str(free)},
            )
        open_count = self._repo.list_page(
            PageRequest.of(1, 1), user_id=int(user_id), status="requested"
        ).total
        if open_count >= MAX_OPEN_WITHDRAWALS:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_TOO_MANY_OPEN", http_status=409)

        try:
            created = self._repo.create(
                WithdrawalRequest(
                    id=0, user_id=int(user_id), amount=amount, payout_method_id=method.id
                )
            )
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        self._notifier.notify([
            FundEvent(
                code=FUND_WITHDRAWAL_REQUESTED,
                about_user_id=created.user_id,
                data={"amount": str(created.amount), "asset": self._asset},
            )
        ])
        return ServiceResult.ok(created)

    def cancel(self, request_id: int, user_id: int) -> ServiceResult[WithdrawalRequest]:
        request = self._repo.get_by_id(int(request_id))
        if request is None or not request.belongs_to(user_id):
            return ServiceResult.fail(code="FUND_WITHDRAWAL_NOT_FOUND", http_status=404)
        request.status = "canceled"
        request.resolved_at = utc_now()
        return self._resolve(request)

    def get(self, request_id: int) -> ServiceResult[WithdrawalRequest]:
        request = self._repo.get_by_id(int(request_id))
        if request is None:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_NOT_FOUND", http_status=404)
        self._with_receipt_names([request])
        return ServiceResult.ok(request)

    def list(
        self, *, page: PageRequest, owner_id: int | None, status: str | None = None
    ) -> ServiceResult[Page[WithdrawalRequest]]:
        if status is not None and status not in WITHDRAWAL_STATUSES:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_INVALID_STATUS", http_status=422)
        result = self._repo.list_page(page, user_id=owner_id, status=status)
        self._with_receipt_names(result.items)
        return ServiceResult.ok(result)

    def get_receipt(
        self, request_id: int, *, user_id: int, is_staff: bool
    ) -> ServiceResult[WithdrawalReceipt]:
        request = self._repo.get_by_id(int(request_id))
        # Otra persona no sabe si el retiro existe
        if request is None or (not is_staff and not request.belongs_to(user_id)):
            return ServiceResult.fail(code="FUND_WITHDRAWAL_NOT_FOUND", http_status=404)
        receipt = self._receipt_repo.get(request.id)
        if receipt is None:
            return ServiceResult.fail(code="FUND_RECEIPT_NOT_FOUND", http_status=404)
        return ServiceResult.ok(receipt)

    # ------------------------------------------------------------------
    # Super admin
    # ------------------------------------------------------------------

    def mark_paid(
        self,
        request_id: int,
        *,
        requester_user_id: int,
        paid_cop_amount: Decimal,
        cop_rate: Decimal,
        payment_reference: str,
        note: str | None = None,
        receipt_filename: str | None = None,
        receipt_base64: str | None = None,
    ) -> ServiceResult[WithdrawalRequest]:
        request = self._repo.get_by_id(int(request_id))
        if request is None:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_NOT_FOUND", http_status=404)
        reference = (payment_reference or "").strip()[:120]
        if paid_cop_amount <= 0 or cop_rate <= 0 or not reference:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_INVALID_PAYMENT", http_status=422)
        receipt = None
        if receipt_base64:
            built = _build_receipt(request.id, receipt_filename, receipt_base64, requester_user_id)
            if not built.success:
                return built
            receipt = built.data
        # Al pagarlo sale del disponible: debe seguir alcanzando
        if self._ledger_repo.bucket_balance(request.user_id, "available") < request.amount:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_EXCEEDS_AVAILABLE", http_status=409)

        request.status = "paid"
        request.paid_cop_amount = paid_cop_amount
        request.cop_rate = cop_rate
        request.payment_reference = reference
        request.resolution_note = (note or "").strip()[:MAX_NOTE_LENGTH] or None
        request.resolved_by_user_id = int(requester_user_id)
        request.resolved_at = utc_now()
        try:
            if not self._repo.update_if_status(request, ["requested"]):
                self._repo.rollback()
                return ServiceResult.fail(code="FUND_WITHDRAWAL_NOT_OPEN", http_status=409)
            self._ledger_repo.add(
                LedgerEntry(
                    id=0,
                    user_id=request.user_id,
                    entry_type="withdrawal",
                    bucket="available",
                    amount=-request.amount,
                    asset=self._asset,
                    ref_type=WITHDRAWAL_REF_TYPE,
                    ref_id=request.id,
                    description=f"Retiro pagado · ref. {reference}",
                    created_by_user_id=int(requester_user_id),
                )
            )
            if receipt is not None:
                self._receipt_repo.save(receipt)
                request.receipt_name = receipt.filename
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        self._notifier.notify([
            FundEvent(
                code=FUND_WITHDRAWAL_PAID,
                user_id=request.user_id,
                data={
                    "amount": str(request.amount),
                    "asset": self._asset,
                    "cop": str(paid_cop_amount),
                    "rate": str(cop_rate),
                    "reference": reference,
                },
            )
        ])
        return ServiceResult.ok(request)

    def reject(
        self, request_id: int, *, requester_user_id: int, note: str | None
    ) -> ServiceResult[WithdrawalRequest]:
        request = self._repo.get_by_id(int(request_id))
        if request is None:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_NOT_FOUND", http_status=404)
        clean = (note or "").strip()[:MAX_NOTE_LENGTH]
        if not clean:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_NOTE_REQUIRED", http_status=422)
        request.status = "rejected"
        request.resolution_note = clean
        request.resolved_by_user_id = int(requester_user_id)
        request.resolved_at = utc_now()
        result = self._resolve(request)
        if result.success:
            self._notifier.notify([
                FundEvent(
                    code=FUND_WITHDRAWAL_REJECTED,
                    user_id=request.user_id,
                    data={"amount": str(request.amount), "asset": self._asset, "note": clean},
                )
            ])
        return result

    def attach_receipt(
        self,
        request_id: int,
        *,
        requester_user_id: int,
        filename: str | None,
        data_base64: str,
    ) -> ServiceResult[WithdrawalRequest]:
        request = self._repo.get_by_id(int(request_id))
        if request is None:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_NOT_FOUND", http_status=404)
        if request.status != "paid":
            return ServiceResult.fail(code="FUND_RECEIPT_NOT_PAID", http_status=409)
        built = _build_receipt(request.id, filename, data_base64, requester_user_id)
        if not built.success:
            return built
        try:
            self._receipt_repo.save(built.data)
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        request.receipt_name = built.data.filename
        return ServiceResult.ok(request)

    def _with_receipt_names(self, requests: list[WithdrawalRequest]) -> None:
        names = self._receipt_repo.names_for([r.id for r in requests])
        for request in requests:
            request.receipt_name = names.get(request.id)

    def _resolve(self, request: WithdrawalRequest) -> ServiceResult[WithdrawalRequest]:
        """Cierra una solicitud abierta sin mover dinero (anular o rechazar)."""
        try:
            if not self._repo.update_if_status(request, ["requested"]):
                self._repo.rollback()
                return ServiceResult.fail(code="FUND_WITHDRAWAL_NOT_OPEN", http_status=409)
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        return ServiceResult.ok(request)


def _build_receipt(
    withdrawal_id: int, filename: str | None, data_base64: str, uploaded_by: int
) -> ServiceResult[WithdrawalReceipt]:
    """Valida el archivo por su contenido (no por el nombre) y su tamaño."""
    content = decode_receipt(data_base64)
    if not content:
        return ServiceResult.fail(code="FUND_RECEIPT_INVALID", http_status=422)
    if len(content) > MAX_RECEIPT_BYTES:
        return ServiceResult.fail(code="FUND_RECEIPT_TOO_LARGE", http_status=422)
    content_type = detect_receipt_type(content)
    if content_type is None:
        return ServiceResult.fail(code="FUND_RECEIPT_INVALID", http_status=422)
    return ServiceResult.ok(
        WithdrawalReceipt(
            withdrawal_id=int(withdrawal_id),
            filename=clean_receipt_name(filename),
            content_type=content_type,
            content=content,
            uploaded_by_user_id=int(uploaded_by),
        )
    )
