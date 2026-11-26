# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/payouts/payout_methods_service.py
#
# CASOS DE USO:
# - networks()                 → redes por las que se envían los retiros
#                                (con comisión y mínimo de Binance en live).
# - list_mine(user_id)         → mis medios de pago (enmascarados).
# - create(...)                → registrar una dirección cripto (red,
#                                dirección y memo si la red lo usa).
# - deactivate(user_id, id)    → dejar de usarlo.
# - details_for_payment(id)    → datos completos (descifrados) para que un
#                                super admin pague un retiro.
#
# REGLAS:
# - Sin bancos (decisión legal, 2026-10-26): el dinero sale solo a
#   direcciones cripto, por una de las redes que el fondo acepta.
# - La dirección se valida por su forma según la red (EVM, Tron, Solana…):
#   un error de tipeo mandaría el dinero a una dirección ajena.
# - Los datos se guardan cifrados (Fernet); en pantalla solo un resumen
#   enmascarado.
# - Un medio nuevo se puede usar a partir de `PAYOUT_METHOD_COOLDOWN_HOURS`
#   (48 h por defecto): si alguien toma la cuenta, no puede desviar un
#   retiro al instante.
# ======================================================================

from __future__ import annotations

from datetime import timedelta

from app.common.contracts import ServiceResult
from app.common.security.credentials_cipher import CredentialsCipher
from app.common.utils import utc_now
from app.modules.fund.domain.payout_repositories import PayoutMethodRepository
from app.modules.fund.domain.withdrawal_entity import (
    PAYOUT_FIELDS,
    PAYOUT_KINDS,
    PAYOUT_OPTIONAL_FIELDS,
    PayoutMethod,
    is_valid_address,
    mask_payout,
    normalize_network,
)
from app.modules.fund.services.payouts.withdraw_networks import (
    WithdrawNetworks,
    WithdrawNetworksReader,
)

MAX_ACTIVE_METHODS = 5
MAX_FIELD_LENGTH = 120


class PayoutMethodsService:

    def __init__(
        self,
        *,
        repo: PayoutMethodRepository,
        cipher: CredentialsCipher,
        cooldown_hours: int,
        networks: WithdrawNetworksReader,
    ):
        self._repo = repo
        self._cipher = cipher
        self._cooldown = timedelta(hours=max(0, int(cooldown_hours)))
        self._networks = networks

    def networks(self) -> ServiceResult[WithdrawNetworks]:
        networks, error = self._networks.read()
        if networks is None:
            return ServiceResult.fail(code=error, http_status=409)
        return ServiceResult.ok(networks)

    def list_mine(self, user_id: int) -> ServiceResult[list[PayoutMethod]]:
        return ServiceResult.ok(self._repo.list_by_user(int(user_id)))

    def create(
        self, *, user_id: int, kind: str, label: str, details: dict[str, str]
    ) -> ServiceResult[PayoutMethod]:
        if kind not in PAYOUT_KINDS:
            return ServiceResult.fail(code="FUND_PAYOUT_INVALID_KIND", http_status=422)
        clean = {key: (details.get(key) or "").strip() for key in PAYOUT_FIELDS[kind]}
        clean["network"] = normalize_network(clean["network"])
        if any(
            (not value and key not in PAYOUT_OPTIONAL_FIELDS) or len(value) > MAX_FIELD_LENGTH
            for key, value in clean.items()
        ):
            return ServiceResult.fail(code="FUND_PAYOUT_INVALID_DETAILS", http_status=422)
        networks, error = self._networks.read()
        if networks is None:
            return ServiceResult.fail(code=error, http_status=409)
        if networks.find(clean["network"]) is None:
            return ServiceResult.fail(code="FUND_PAYOUT_INVALID_NETWORK", http_status=422)
        if not is_valid_address(clean["network"], clean["address"]):
            return ServiceResult.fail(code="FUND_PAYOUT_INVALID_ADDRESS", http_status=422)
        clean_label = (label or "").strip()[:80]
        if not clean_label:
            return ServiceResult.fail(code="FUND_PAYOUT_INVALID_DETAILS", http_status=422)
        if len(self._repo.list_by_user(int(user_id))) >= MAX_ACTIVE_METHODS:
            return ServiceResult.fail(code="FUND_PAYOUT_TOO_MANY", http_status=409)

        method = PayoutMethod(
            id=0,
            user_id=int(user_id),
            kind=kind,
            label=clean_label,
            masked=mask_payout(kind, clean),
            usable_from=utc_now() + self._cooldown,
        )
        try:
            saved = self._repo.create(method, self._cipher.encrypt_dict(clean))
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        return ServiceResult.ok(saved)

    def deactivate(self, user_id: int, method_id: int) -> ServiceResult[None]:
        method = self._repo.get_by_id(int(method_id))
        if method is None or not method.belongs_to(user_id) or not method.is_active:
            return ServiceResult.fail(code="FUND_PAYOUT_NOT_FOUND", http_status=404)
        try:
            self._repo.deactivate(method.id)
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        return ServiceResult.ok(None)

    def details_for_payment(self, method_id: int) -> ServiceResult[PayoutMethod]:
        method = self._repo.get_by_id(int(method_id))
        token = self._repo.get_encrypted_details(int(method_id))
        if method is None or token is None:
            return ServiceResult.fail(code="FUND_PAYOUT_NOT_FOUND", http_status=404)
        try:
            method.details = self._cipher.decrypt(token)
        except Exception:
            return ServiceResult.fail(code="FUND_PAYOUT_UNREADABLE", http_status=500)
        return ServiceResult.ok(method)
