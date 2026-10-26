# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/services/wallet/ensure_platform_wallet_service.py
#
# CASO DE USO:
# - Garantizar que exista la billetera única de la plataforma: la cuenta
#   live "Billetera Binance" y la fila de `platform_wallet` que apunta a
#   ella. Nadie la elige ni la crea a mano: la app la arma sola la primera
#   vez que alguien la necesita (página Billetera, scheduler, fondo,
#   crear un agente real).
#
# REGLAS:
# - Idempotente: si ya hay billetera sobre una cuenta live activa, no
#   escribe nada.
# - Si la billetera apuntaba a una cuenta paper (datos de desarrollo de
#   antes del 2026-10-26), se crea la cuenta live y se re-apunta.
# - La cuenta queda a nombre del primer super admin activo (la columna
#   `accounts.user_id` es obligatoria); sin super admin todavía no se puede
#   crear y devuelve None.
# - Las credenciales no viven aquí: salen del `.env` (BINANCE_API_KEY /
#   BINANCE_API_SECRET) al armar el cliente del exchange.
# - Confirma (commit) solo cuando crea algo: es una pieza aparte que no
#   depende del caso de uso que la llama.
# ======================================================================

from __future__ import annotations

from typing import Callable

from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.accounts.domain.platform_wallet_entity import PlatformWallet
from app.modules.accounts.domain.platform_wallet_repository import PlatformWalletRepository
from app.modules.market.domain.ccxt_exchanges import PLATFORM_EXCHANGE_NAME
from app.modules.market.domain.exchange_repository import ExchangeRepository

PLATFORM_WALLET_ACCOUNT_NAME = f"Billetera {PLATFORM_EXCHANGE_NAME}"


class EnsurePlatformWalletService:

    def __init__(
        self,
        *,
        wallet_repo: PlatformWalletRepository,
        account_repo: AccountRepository,
        exchange_repo: ExchangeRepository,
        owner_resolver: Callable[[], int | None],
        base_asset: str,
    ):
        self._wallet_repo = wallet_repo
        self._account_repo = account_repo
        self._exchange_repo = exchange_repo
        self._owner_resolver = owner_resolver
        self._base_asset = base_asset.upper()

    def ensure(self) -> Account | None:
        """La cuenta de la billetera de Binance (creándola si falta), o None."""
        wallet = self._wallet_repo.get()
        if wallet is not None:
            account = self._account_repo.get_by_id(wallet.account_id)
            if account is not None and account.mode == "live":
                return account

        exchange = self._exchange_repo.get_by_name(PLATFORM_EXCHANGE_NAME)
        owner_id = self._owner_resolver()
        if exchange is None or owner_id is None:
            return None

        try:
            account = self._account_repo.create(
                Account(
                    id=0,
                    user_id=int(owner_id),
                    exchange_id=exchange.id,
                    name=PLATFORM_WALLET_ACCOUNT_NAME,
                    mode="live",
                    base_currency=self._base_asset,
                    status="active",
                    meta={"platform_wallet": True},
                )
            )
            self._wallet_repo.save(
                PlatformWallet(
                    account_id=account.id,
                    base_asset=self._base_asset,
                    updated_by_user_id=int(owner_id),
                )
            )
            self._wallet_repo.commit()
        except Exception:
            self._wallet_repo.rollback()
            raise
        return account
