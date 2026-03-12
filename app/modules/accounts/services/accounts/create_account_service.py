# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.common.security.credentials_cipher import CredentialsCipher
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.market.domain.exchange_repository import ExchangeRepository


class CreateAccountService:
    """
    Crea una nueva cuenta de trading.

    Reglas de negocio:
    - Si se proveen credenciales, se cifran y se almacenan en meta['enc_creds'].
    - El exchange debe existir si se especifica exchange_id.
    - Modo válido: paper | live.
    """

    def __init__(
        self,
        account_repo: AccountRepository,
        exchange_repo: ExchangeRepository,
        session: Session,
        cipher: CredentialsCipher,
    ):
        self._account_repo = account_repo
        self._exchange_repo = exchange_repo
        self._session = session
        self._cipher = cipher

    def create(
        self,
        user_id: int,
        name: str,
        mode: str,
        base_currency: str = "USD",
        exchange_id: Optional[int] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        credentials_label: Optional[str] = None,
    ) -> ServiceResult[Account]:
        # Validar modo
        if mode not in Account.VALID_MODES:
            return ServiceResult.fail(code="ACCOUNT_INVALID_MODE", http_status=422)

        # Validar exchange si se especifica
        if exchange_id is not None:
            exchange = self._exchange_repo.get_by_id(exchange_id)
            if exchange is None:
                return ServiceResult.fail(code="EXCHANGE_NOT_FOUND", http_status=404)

        # Construir meta con credenciales cifradas si se proveen
        meta: dict = {}
        credentials_ref: Optional[str] = None

        if api_key and api_secret:
            meta["enc_creds"] = self._cipher.encrypt(api_key=api_key, api_secret=api_secret)
            credentials_ref = credentials_label or "encrypted"

        account = Account(
            id=0,
            user_id=user_id,
            exchange_id=exchange_id,
            name=name.strip(),
            mode=mode,
            base_currency=base_currency.upper(),
            status="active",
            credentials_ref=credentials_ref,
            meta=meta,
        )

        created = self._account_repo.create(account)
        self._session.commit()
        return ServiceResult.ok(data=created)
