# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.common.security.credentials_cipher import CredentialsCipher
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.market.domain.exchange_repository import ExchangeRepository


class UpdateAccountService:
    """
    Actualiza una cuenta de trading.

    Reglas de negocio:
    - Solo el dueño o un admin puede actualizar la cuenta.
    - Si se proveen nuevas credenciales, se re-cifran (reemplaza las anteriores).
    - No se permite cambiar el user_id ni el modo (paper↔live) tras la creación.
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

    def update(
        self,
        account_id: int,
        requester_user_id: int,
        is_admin: bool = False,
        name: Optional[str] = None,
        status: Optional[str] = None,
        exchange_id: Optional[int] = None,
        base_currency: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        credentials_label: Optional[str] = None,
    ) -> ServiceResult[Account]:
        account = self._account_repo.get_by_id(account_id)

        if account is None:
            return ServiceResult.fail(code="ACCOUNT_NOT_FOUND", http_status=404)

        if not is_admin and not account.belongs_to(requester_user_id):
            return ServiceResult.fail(code="ACCOUNT_FORBIDDEN", http_status=403)

        # Validar status si se provee
        if status is not None and status not in Account.VALID_STATUSES:
            return ServiceResult.fail(code="ACCOUNT_INVALID_STATUS", http_status=422)

        # Validar exchange si se cambia
        if exchange_id is not None:
            exchange = self._exchange_repo.get_by_id(exchange_id)
            if exchange is None:
                return ServiceResult.fail(code="EXCHANGE_NOT_FOUND", http_status=404)
            account.exchange_id = exchange_id

        # Aplicar cambios
        if name is not None:
            account.name = name.strip()
        if status is not None:
            account.status = status
        if base_currency is not None:
            account.base_currency = base_currency.upper()

        # Re-cifrar credenciales si se proveen nuevas
        if api_key and api_secret:
            account.meta["enc_creds"] = self._cipher.encrypt(
                api_key=api_key, api_secret=api_secret
            )
            account.credentials_ref = credentials_label or "encrypted"

        updated = self._account_repo.update(account)
        self._session.commit()
        return ServiceResult.ok(data=updated)
