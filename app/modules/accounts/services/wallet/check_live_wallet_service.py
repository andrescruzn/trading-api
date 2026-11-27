# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/services/wallet/check_live_wallet_service.py
#
# CASO DE USO:
# - Confirmar que la billetera de Binance está lista para operar en real
#   antes de crear o iniciar un agente real (lo usa el módulo bots).
#
# REGLAS:
# - La decide `live_block_code` (domain/platform_wallet_rules.py).
# - No llama a Binance: usa la última sincronización guardada.
# - Devuelve la cuenta de la billetera para ligarla al agente.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.platform_wallet_repository import PlatformWalletRepository
from app.modules.accounts.domain.platform_wallet_rules import live_block_code
from app.modules.accounts.services.wallet.ensure_platform_wallet_service import (
    EnsurePlatformWalletService,
)


class CheckLiveWalletService:
    """
    Revisa si la billetera de Binance sirve para un agente real.

    Errores (409, todos):
    - WALLET_CREDENTIALS_MISSING: faltan BINANCE_API_KEY / BINANCE_API_SECRET.
    - WALLET_UNAVAILABLE: no se pudo crear la billetera (sin super admin
      activo o sin Binance en `exchanges`).
    - WALLET_EXCHANGE_AUTH_FAILED: Binance rechazó las llaves en la última
      sincronización.
    - WALLET_NOT_VERIFIED: la billetera nunca se ha sincronizado.
    """

    def __init__(
        self,
        *,
        wallet_repo: PlatformWalletRepository,
        ensure: EnsurePlatformWalletService,
        credentials_configured: bool,
    ):
        self._wallet_repo = wallet_repo
        self._ensure = ensure
        self._credentials_configured = credentials_configured

    def check(self) -> ServiceResult[Account]:
        account = self._ensure.ensure()
        wallet = self._wallet_repo.get() if account is not None else None

        code = live_block_code(self._credentials_configured, wallet)
        if code is not None:
            return ServiceResult.fail(code=code, http_status=409)
        return ServiceResult.ok(data=account)
