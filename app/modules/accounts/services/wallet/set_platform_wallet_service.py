# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/services/wallet/set_platform_wallet_service.py
#
# CASO DE USO:
# - Un super admin elige qué cuenta de exchange es la billetera de la
#   plataforma (fondo común: hay una sola).
#
# REGLAS:
# - La cuenta debe existir, estar activa y tener exchange.
# - Una cuenta live necesita API key: sin ella no se puede leer el saldo.
#   Una cuenta paper se acepta (desarrollo): su saldo es el registrado a
#   mano.
# - Cambiar de cuenta borra el estado de la última sincronización (era de
#   otra cuenta). Elegir la misma no escribe nada.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.accounts.domain.platform_wallet_entity import PlatformWallet
from app.modules.accounts.domain.platform_wallet_repository import PlatformWalletRepository


class SetPlatformWalletService:

    def __init__(
        self,
        *,
        wallet_repo: PlatformWalletRepository,
        account_repo: AccountRepository,
        base_asset: str,
    ):
        self._wallet_repo = wallet_repo
        self._account_repo = account_repo
        self._base_asset = base_asset.upper()

    def set(self, account_id: int, requester_user_id: int) -> ServiceResult[PlatformWallet]:
        account = self._account_repo.get_by_id(int(account_id))
        if account is None:
            return ServiceResult.fail(code="WALLET_ACCOUNT_NOT_FOUND", http_status=404)
        if not account.is_active():
            return ServiceResult.fail(code="WALLET_ACCOUNT_INACTIVE", http_status=409)
        if account.exchange_id is None:
            return ServiceResult.fail(code="WALLET_ACCOUNT_NO_EXCHANGE", http_status=422)
        if account.mode == "live" and not account.meta.get("enc_creds"):
            return ServiceResult.fail(code="WALLET_ACCOUNT_NO_CREDENTIALS", http_status=422)

        current = self._wallet_repo.get()
        if current is not None and current.account_id == account.id:
            return ServiceResult.ok(current)

        wallet = PlatformWallet(
            account_id=account.id,
            base_asset=self._base_asset,
            updated_by_user_id=int(requester_user_id),
        )
        try:
            saved = self._wallet_repo.save(wallet)
            self._wallet_repo.commit()
        except Exception:
            self._wallet_repo.rollback()
            raise
        return ServiceResult.ok(saved)
