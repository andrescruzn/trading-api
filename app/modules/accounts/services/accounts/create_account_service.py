# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from app.common.contracts import ServiceResult
from app.common.security.credentials_cipher import CredentialsCipher
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.market.domain.ccxt_exchanges import PLATFORM_EXCHANGE_NAME
from app.modules.market.domain.exchange_repository import ExchangeRepository


class CreateAccountService:
    """
    Crea una nueva cuenta de trading.

    Reglas de negocio:
    - Si se proveen credenciales, se cifran y se almacenan en meta['enc_creds'].
    - Toda cuenta queda en el exchange de la plataforma (Binance), también
      las de práctica, que usan sus precios.
    - Modo válido: paper | live.
    """

    def __init__(
        self,
        account_repo: AccountRepository,
        exchange_repo: ExchangeRepository,
        cipher: CredentialsCipher,
    ):
        self._account_repo = account_repo
        self._exchange_repo = exchange_repo
        self._cipher = cipher

    def create(
        self,
        user_id: int,
        name: str,
        mode: str,
        base_currency: str = "USD",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        credentials_label: Optional[str] = None,
    ) -> ServiceResult[Account]:
        # Validar modo
        if mode not in Account.VALID_MODES:
            return ServiceResult.fail(code="ACCOUNT_INVALID_MODE", http_status=422)

        exchange = self._exchange_repo.get_by_name(PLATFORM_EXCHANGE_NAME)
        if exchange is None:
            return ServiceResult.fail(code="PLATFORM_EXCHANGE_MISSING", http_status=409)

        # Construir meta con credenciales cifradas si se proveen
        meta: dict = {}
        credentials_ref: Optional[str] = None

        if api_key and api_secret:
            meta["enc_creds"] = self._cipher.encrypt(api_key=api_key, api_secret=api_secret)
            credentials_ref = credentials_label or "encrypted"

        account = Account(
            id=0,
            user_id=user_id,
            exchange_id=exchange.id,
            name=name.strip(),
            mode=mode,
            base_currency=base_currency.upper(),
            status="active",
            credentials_ref=credentials_ref,
            meta=meta,
        )

        created = self._account_repo.create(account)
        self._account_repo.commit()
        return ServiceResult.ok(data=created)
