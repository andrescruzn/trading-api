# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/deposits/unclaimed_deposits_service.py
#
# CASOS DE USO:
# - list()   → depósitos que entraron a la billetera (estado `ok` en el
#              exchange, últimos UNCLAIMED_WINDOW_DAYS días) sin solicitud de
#              nadie. Explican una diferencia de conciliación (staff).
# - assign() → un super admin asigna uno de ellos a una persona con una nota:
#              se crea la solicitud ya confirmada y se acredita.
#
# REGLAS:
# - Solo con billetera live (en paper no hay depósitos reales).
# - El txid debe estar en el exchange y sin solicitud (si no, 409).
# ======================================================================

from __future__ import annotations

from datetime import timedelta

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.accounts.domain.wallet_gateway import (
    ExchangeDeposit,
    WalletGateway,
    WalletGatewayError,
)
from app.modules.fund.domain.deposit_request_entity import DepositRequest, normalize_txid
from app.modules.fund.domain.fund_repositories import DepositRequestRepository, LedgerRepository
from app.modules.fund.services.deposits.deposit_crediting import DepositCreditor
from app.modules.fund.services.wallet_context import WalletContext, WalletContextResolver
from app.modules.users.domain import UserRepository

UNCLAIMED_WINDOW_DAYS = 30
MAX_NOTE_LENGTH = 500


class UnclaimedDepositsService:

    def __init__(
        self,
        *,
        deposit_repo: DepositRequestRepository,
        ledger_repo: LedgerRepository,
        user_repo: UserRepository,
        wallet_resolver: WalletContextResolver,
        gateway: WalletGateway,
    ):
        self._deposit_repo = deposit_repo
        self._user_repo = user_repo
        self._wallet_resolver = wallet_resolver
        self._gateway = gateway
        self._creditor = DepositCreditor(deposit_repo, ledger_repo)

    def list(self) -> ServiceResult[list[ExchangeDeposit]]:
        context, error = self._wallet_resolver.resolve()
        if context is None:
            return ServiceResult.fail(code=error, http_status=409)
        if not context.is_live:
            return ServiceResult.ok([])
        try:
            return ServiceResult.ok(self._unclaimed(context))
        except WalletGatewayError as exc:
            return ServiceResult.fail(code=exc.code, http_status=502)

    def assign(
        self, *, txid: str, user_id: int, requester_user_id: int, note: str | None
    ) -> ServiceResult[DepositRequest]:
        clean_note = (note or "").strip()[:MAX_NOTE_LENGTH]
        if not clean_note:
            return ServiceResult.fail(code="FUND_DEPOSIT_NOTE_REQUIRED", http_status=422)
        if self._user_repo.get_by_id(int(user_id)) is None:
            return ServiceResult.fail(code="FUND_USER_NOT_FOUND", http_status=404)

        context, error = self._wallet_resolver.resolve()
        if context is None:
            return ServiceResult.fail(code=error, http_status=409)
        if not context.is_live:
            return ServiceResult.fail(code="FUND_WALLET_NOT_LIVE", http_status=409)

        clean_txid = normalize_txid(txid)
        try:
            deposit = next(
                (d for d in self._unclaimed(context) if normalize_txid(d.txid) == clean_txid),
                None,
            )
        except WalletGatewayError as exc:
            return ServiceResult.fail(code=exc.code, http_status=502)
        if deposit is None:
            return ServiceResult.fail(code="FUND_UNCLAIMED_NOT_FOUND", http_status=409)

        now = utc_now()
        try:
            request = self._deposit_repo.create(
                DepositRequest(
                    id=0,
                    user_id=int(user_id),
                    asset=context.asset,
                    network=deposit.network or "—",
                    txid=clean_txid,
                    declared_amount=deposit.amount,
                    credited_amount=deposit.amount,
                    address_from=deposit.address_from,
                    exchange_deposit_id=deposit.exchange_id,
                    exchange_status=deposit.status,
                    expires_at=now,
                )
            )
            self._creditor.confirm(
                request,
                amount=deposit.amount,
                now=now,
                expected=["pending"],
                resolved_by_user_id=int(requester_user_id),
                note=clean_note,
            )
            self._deposit_repo.commit()
        except Exception:
            self._deposit_repo.rollback()
            raise
        return ServiceResult.ok(request)

    def _unclaimed(self, context: WalletContext) -> list[ExchangeDeposit]:
        since = utc_now() - timedelta(days=UNCLAIMED_WINDOW_DAYS)
        deposits = [
            d
            for d in self._gateway.fetch_deposits(context.account, context.asset, since)
            if d.status == "ok" and d.amount > 0
        ]
        claimed = self._deposit_repo.txids_in([normalize_txid(d.txid) for d in deposits])
        return [d for d in deposits if normalize_txid(d.txid) not in claimed]
