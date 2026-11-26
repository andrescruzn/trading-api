# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/payouts/withdrawal_service.py
#
# CASOS DE USO:
# - free_available(user_id) → lo que la persona puede retirar o reinvertir:
#                             disponible − retiros sin pagar − asignaciones en
#                             cola desde el disponible.
# - create(...)             → pedir un retiro a una dirección cripto propia.
# - cancel(...)             → anularlo mientras no se haya pagado.
# - list(...)               → los propios; el staff ve todos.
# - lookup(...)             → un super admin pega el txid del envío y la app
#                             lo busca en el historial de retiros de Binance.
# - mark_paid(...)          → registra el envío (txid, enviado, comisión de
#                             red); sale del saldo (asiento `withdrawal`).
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
# - Sin bancos (decisión legal, 2026-10-26): un super admin envía USDT desde
#   Binance a la dirección de la persona. La comisión de red la paga ella:
#   pide 100, recibe 100 − comisión, y del libro salen los 100.
# - Con billetera live el envío se comprueba contra Binance antes de darlo
#   por pagado: debe estar completado y haber ido a la dirección y red de la
#   persona (si no, se bloquea: no hay nota que lo arregle). Si Binance no lo
#   muestra o el monto no cuadra, solo se registra con una nota. La API key
#   solo LEE el historial: no necesita permiso de retiro.
# ======================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from app.common.contracts import Page, PageRequest, ServiceResult
from app.common.security.credentials_cipher import CredentialsCipher
from app.common.utils import to_iso_utc, utc_now
from app.modules.accounts.domain.wallet_gateway import (
    ExchangeWithdrawal,
    WalletGateway,
    WalletGatewayError,
)
from app.modules.fund.domain.deposit_request_entity import is_valid_txid, normalize_txid
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
    PAYMENT_TOLERANCE_RATIO,
    WITHDRAWAL_STATUSES,
    WithdrawalReceipt,
    WithdrawalRequest,
    clean_receipt_name,
    decode_receipt,
    detect_receipt_type,
    explorer_url,
    normalize_network,
    same_address,
    short_address,
)
from app.modules.fund.services.payouts.withdraw_networks import WithdrawNetworksReader
from app.modules.fund.services.wallet_context import WalletContextResolver

logger = logging.getLogger(__name__)

WITHDRAWAL_REF_TYPE = "withdrawal_request"
MAX_OPEN_WITHDRAWALS = 5
MAX_NOTE_LENGTH = 500
# Margen hacia atrás al buscar el envío en Binance (relojes, zonas)
_LOOKBACK = timedelta(days=1)


@dataclass(frozen=True)
class WithdrawalCheck:
    """Lo que dice Binance de un txid, comparado con el retiro pedido."""

    txid: str
    is_live: bool
    found: ExchangeWithdrawal | None
    # Destino de la persona (red y dirección del medio de pago)
    network: str
    address: str
    memo: str | None
    # None = no se pudo comparar (sin dato de Binance)
    address_matches: bool | None = None
    amount_matches: bool | None = None
    # Binance no respondió: se registra como "no encontrado" (con nota)
    exchange_error: str | None = None

    @property
    def completed(self) -> bool:
        return self.found is not None and self.found.status == "ok"


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
        cipher: CredentialsCipher,
        networks: WithdrawNetworksReader,
        wallet_resolver: WalletContextResolver,
        gateway: WalletGateway,
        notifier: FundNotifier | None = None,
    ):
        self._notifier = notifier or NullFundNotifier()
        self._cipher = cipher
        self._networks = networks
        self._wallet_resolver = wallet_resolver
        self._gateway = gateway
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
                meta={"usable_from": to_iso_utc(method.usable_from)},
            )
        details = self._details(method.id)
        if details is None:
            return ServiceResult.fail(code="FUND_PAYOUT_UNREADABLE", http_status=500)
        networks, _ = self._networks.read()
        info = networks.find(details.get("network")) if networks else None
        if networks is not None and info is None:
            # La red dejó de aceptarse después de registrar la dirección
            return ServiceResult.fail(code="FUND_PAYOUT_INVALID_NETWORK", http_status=409)
        if info is not None:
            # Binance exige el mínimo y descuenta la comisión: debe quedar algo
            minimum = max(info.min_amount or Decimal("0"), info.fee or Decimal("0"))
            if amount < minimum or (info.fee is not None and amount <= info.fee):
                return ServiceResult.fail(
                    code="FUND_WITHDRAWAL_BELOW_NETWORK_MIN",
                    http_status=422,
                    meta={"minimum": str(minimum), "fee": str(info.fee or 0)},
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

    def lookup(self, request_id: int, txid: str) -> ServiceResult[WithdrawalCheck]:
        """Busca el envío en Binance sin cambiar nada (para revisar antes de registrar)."""
        request = self._repo.get_by_id(int(request_id))
        if request is None:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_NOT_FOUND", http_status=404)
        return self._check(request, txid)

    def mark_paid(
        self,
        request_id: int,
        *,
        requester_user_id: int,
        txid: str,
        sent_amount: Decimal | None = None,
        network_fee: Decimal | None = None,
        note: str | None = None,
        receipt_filename: str | None = None,
        receipt_base64: str | None = None,
    ) -> ServiceResult[WithdrawalRequest]:
        request = self._repo.get_by_id(int(request_id))
        if request is None:
            return ServiceResult.fail(code="FUND_WITHDRAWAL_NOT_FOUND", http_status=404)
        if request.status != "requested":
            return ServiceResult.fail(code="FUND_WITHDRAWAL_NOT_OPEN", http_status=409)
        checked = self._check(request, txid)
        if not checked.success:
            return checked
        check = checked.data
        clean_note = (note or "").strip()[:MAX_NOTE_LENGTH] or None

        found = check.found
        if found is not None:
            if found.status == "pending":
                return ServiceResult.fail(code="FUND_WITHDRAWAL_TX_PENDING", http_status=409)
            if found.status != "ok":
                return ServiceResult.fail(code="FUND_WITHDRAWAL_TX_FAILED", http_status=409)
            if check.address_matches is False:
                return ServiceResult.fail(code="FUND_WITHDRAWAL_ADDRESS_MISMATCH", http_status=409)
            sent, fee = found.amount, found.fee
            # Sin dirección en Binance o con otro monto: solo con explicación
            if (check.address_matches is None or check.amount_matches is False) and not clean_note:
                return ServiceResult.fail(code="FUND_WITHDRAWAL_PAYMENT_NOTE_REQUIRED", http_status=422)
        else:
            # Sin respaldo de Binance (práctica, o no aparece aún): datos a mano
            if sent_amount is None or sent_amount <= 0 or (network_fee is not None and network_fee < 0):
                return ServiceResult.fail(code="FUND_WITHDRAWAL_INVALID_PAYMENT", http_status=422)
            sent, fee = sent_amount, network_fee or Decimal("0")
            if check.is_live and not clean_note:
                return ServiceResult.fail(code="FUND_WITHDRAWAL_TX_NOT_FOUND", http_status=409)
            if not _amounts_match(request.amount, sent, fee) and not clean_note:
                return ServiceResult.fail(code="FUND_WITHDRAWAL_PAYMENT_NOTE_REQUIRED", http_status=422)

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
        request.txid = check.txid
        request.network = check.network
        request.sent_amount = sent
        request.network_fee = fee
        request.exchange_withdrawal_id = found.exchange_id if found else None
        request.resolution_note = clean_note
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
                    description=f"Retiro enviado · {check.network} · {short_address(check.txid)}",
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
                    "sent": str(sent),
                    "fee": str(fee),
                    "network": check.network,
                    "address": short_address(check.address),
                    "txid": check.txid,
                    "explorer_url": explorer_url(check.network, check.txid) or "",
                },
            )
        ])
        return ServiceResult.ok(request)

    def _check(self, request: WithdrawalRequest, txid: str) -> ServiceResult[WithdrawalCheck]:
        """Normaliza el txid, lee el destino de la persona y busca el envío en Binance."""
        clean = normalize_txid(txid)
        if not is_valid_txid(clean):
            return ServiceResult.fail(code="FUND_WITHDRAWAL_INVALID_TXID", http_status=422)
        if self._repo.txid_taken(clean):
            return ServiceResult.fail(code="FUND_WITHDRAWAL_TXID_TAKEN", http_status=409)
        details = self._details(request.payout_method_id)
        if details is None:
            return ServiceResult.fail(code="FUND_PAYOUT_UNREADABLE", http_status=500)
        context, error = self._wallet_resolver.resolve()
        if context is None:
            return ServiceResult.fail(code=error, http_status=409)

        network = normalize_network(details.get("network"))
        address = details.get("address") or ""
        memo = details.get("memo") or None
        base = dict(txid=clean, is_live=context.is_live, network=network, address=address, memo=memo)
        if not context.is_live:
            return ServiceResult.ok(WithdrawalCheck(found=None, **base))
        try:
            since = (request.created_at or utc_now()) - _LOOKBACK
            withdrawals = self._gateway.fetch_withdrawals(context.account, context.asset, since)
        except WalletGatewayError as exc:
            logger.warning("[Fund] No se pudieron leer los retiros (%s): %s", exc.code, exc)
            return ServiceResult.ok(WithdrawalCheck(found=None, exchange_error=exc.code, **base))

        found = next((w for w in withdrawals if normalize_txid(w.txid) == clean), None)
        if found is None:
            return ServiceResult.ok(WithdrawalCheck(found=None, **base))
        address_matches = None
        if found.address:
            address_matches = (
                same_address(network, found.address, address)
                and (found.network is None or normalize_network(found.network) == network)
                # Con memo, Binance debe haberlo enviado igual (si no, el dinero no llega)
                and (memo is None or (found.tag or "") == memo)
            )
        return ServiceResult.ok(
            WithdrawalCheck(
                found=found,
                address_matches=address_matches,
                amount_matches=_amounts_match(request.amount, found.amount, found.fee),
                **base,
            )
        )

    def _details(self, method_id: int) -> dict[str, str] | None:
        token = self._payout_repo.get_encrypted_details(int(method_id))
        if token is None:
            return None
        try:
            return self._cipher.decrypt(token)
        except Exception:
            return None

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


def _amounts_match(requested: Decimal, sent: Decimal, fee: Decimal) -> bool:
    """Lo que salió de la billetera (enviado + comisión) ≈ lo pedido."""
    return abs((sent + fee) - requested) <= requested * PAYMENT_TOLERANCE_RATIO


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
