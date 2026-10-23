# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/services/wallet/sync_wallet_service.py
#
# CASO DE USO:
# - Leer el saldo de la billetera de la plataforma, valorarlo en la moneda
#   base y guardar una foto (`wallet_snapshots`). Lo llaman el scheduler
#   (cada WALLET_SYNC_INTERVAL_SECONDS) y "Sincronizar ahora".
#
# REGLAS:
# - Cuenta live: el saldo viene del exchange y se graba también en
#   `account_balances` (misma hora para todos los activos), así el 1 % de
#   los agentes usa el saldo real. Un activo que tenía saldo y ya no
#   aparece se graba en 0 para que su último balance no quede viejo; la
#   moneda base siempre se graba.
# - Cuenta paper (desarrollo): la foto se arma con los últimos balances
#   registrados a mano; no se escribe `account_balances`.
# - Los precios fallan sin tumbar la sincronización: los activos sin precio
#   quedan en `missing_prices` y no suman al total.
# - Si falla la lectura del saldo, se guarda el código en la billetera
#   (`last_sync_error`) y el servicio devuelve el error.
# ======================================================================

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.accounts.domain.account_balance_entity import AccountBalance
from app.modules.accounts.domain.account_balance_repository import AccountBalanceRepository
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.accounts.domain.platform_wallet_entity import PlatformWallet
from app.modules.accounts.domain.platform_wallet_repository import (
    PlatformWalletRepository,
    WalletSnapshotRepository,
)
from app.modules.accounts.domain.wallet_gateway import WalletGateway, WalletGatewayError
from app.modules.accounts.domain.wallet_snapshot_entity import (
    AssetBalance,
    WalletSnapshot,
    value_wallet,
)

logger = logging.getLogger(__name__)

# Errores de configuración de la cuenta (422) vs. del exchange (502/503)
_GATEWAY_HTTP_STATUS: dict[str, int] = {
    "WALLET_ACCOUNT_NO_EXCHANGE": 422,
    "WALLET_ACCOUNT_NO_CREDENTIALS": 422,
    "WALLET_EXCHANGE_NOT_SUPPORTED": 422,
    "WALLET_CREDENTIALS_UNREADABLE": 422,
    "WALLET_EXCHANGE_AUTH_FAILED": 502,
    "WALLET_EXCHANGE_UNAVAILABLE": 503,
}


class SyncWalletService:

    def __init__(
        self,
        *,
        wallet_repo: PlatformWalletRepository,
        snapshot_repo: WalletSnapshotRepository,
        account_repo: AccountRepository,
        balance_repo: AccountBalanceRepository,
        gateway: WalletGateway,
    ):
        self._wallet_repo = wallet_repo
        self._snapshot_repo = snapshot_repo
        self._account_repo = account_repo
        self._balance_repo = balance_repo
        self._gateway = gateway

    def sync(self) -> ServiceResult[WalletSnapshot]:
        wallet = self._wallet_repo.get()
        if wallet is None:
            return ServiceResult.fail(code="WALLET_NOT_CONFIGURED", http_status=404)

        account = self._account_repo.get_by_id(wallet.account_id)
        if account is None:
            return ServiceResult.fail(code="WALLET_ACCOUNT_NOT_FOUND", http_status=404)
        if not account.is_active():
            return self._fail(wallet, "WALLET_ACCOUNT_INACTIVE", 409)

        now = utc_now()
        previous = self._balance_repo.list_latest_by_account(account.id)

        if account.mode == "live":
            try:
                balances = self._gateway.fetch_balances(account)
            except WalletGatewayError as exc:
                logger.warning("[Wallet] Sincronización fallida (%s): %s", exc.code, exc)
                return self._fail(wallet, exc.code, _GATEWAY_HTTP_STATUS.get(exc.code, 502))
            source = "exchange"
        else:
            balances = [AssetBalance(b.asset.upper(), b.free, b.locked) for b in previous]
            source = "manual"

        base = wallet.base_asset.upper()
        snapshot = value_wallet(
            account_id=account.id,
            base_asset=base,
            balances=balances,
            prices=self._prices(account, balances, base),
            source=source,
            ts=now,
        )

        try:
            if source == "exchange":
                self._record_balances(account.id, balances, previous, base, now)
            saved = self._snapshot_repo.record(snapshot)
            wallet.mark_synced(now)
            self._wallet_repo.save(wallet)
            self._wallet_repo.commit()
        except Exception:
            self._wallet_repo.rollback()
            raise
        return ServiceResult.ok(saved)

    # ==================================================================
    # Helpers
    # ==================================================================

    def _prices(
        self, account: Account, balances: list[AssetBalance], base: str
    ) -> dict[str, Decimal]:
        assets = [b.asset for b in balances if b.total > 0 and b.asset.upper() != base]
        if not assets:
            return {}
        try:
            return self._gateway.fetch_prices(account, assets, base)
        except WalletGatewayError as exc:
            # Sin precios la foto sale con esos activos en `missing_prices`
            logger.warning("[Wallet] Sin precios (%s): %s", exc.code, exc)
            return {}

    def _record_balances(
        self,
        account_id: int,
        balances: list[AssetBalance],
        previous: list[AccountBalance],
        base: str,
        ts: datetime,
    ) -> None:
        current = {b.asset.upper(): b for b in balances}
        had_balance = {b.asset.upper() for b in previous if b.total > 0}
        zero = Decimal("0")
        for asset in sorted(set(current) | had_balance | {base}):
            balance = current.get(asset) or AssetBalance(asset, zero, zero)
            # Se graba lo que tiene saldo, lo que lo tenía (ahora en 0) y la
            # moneda base; el resto de activos en 0 del exchange no.
            if balance.total <= 0 and asset not in had_balance and asset != base:
                continue
            self._balance_repo.record(
                AccountBalance(
                    id=0,
                    account_id=account_id,
                    asset=asset,
                    free=balance.free,
                    locked=balance.locked,
                    ts=ts,
                )
            )

    def _fail(self, wallet: PlatformWallet, code: str, http_status: int) -> ServiceResult:
        try:
            wallet.mark_sync_failed(code)
            self._wallet_repo.save(wallet)
            self._wallet_repo.commit()
        except Exception:
            self._wallet_repo.rollback()
            raise
        return ServiceResult.fail(code=code, http_status=http_status)
