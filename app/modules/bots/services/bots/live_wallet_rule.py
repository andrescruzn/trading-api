# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/live_wallet_rule.py
#
# REGLA (billetera lista para agentes reales, 2026-11-27):
# - Un agente real solo se crea o se inicia (o reanuda) si la billetera de
#   Binance está lista: llaves en el `.env` y una sincronización que las
#   confirmó. Sin esto el agente se creaba igual y cada orden fallaba
#   después con EXCHANGE_CREDENTIALS_MISSING.
# - Quién decide si está lista: accounts (CheckLiveWalletService); aquí
#   solo se traduce su código a uno del módulo bots.
# ======================================================================

from __future__ import annotations

from typing import Callable

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_entity import Account

# Revisión inyectada desde el provider: la billetera o el motivo del bloqueo
LiveWalletChecker = Callable[[], ServiceResult[Account]]

_BOT_CODES: dict[str, str] = {
    "WALLET_CREDENTIALS_MISSING":  "BOT_WALLET_NOT_CONFIGURED",
    "WALLET_UNAVAILABLE":          "BOT_WALLET_UNAVAILABLE",
    "WALLET_EXCHANGE_AUTH_FAILED": "BOT_WALLET_AUTH_FAILED",
    "WALLET_NOT_VERIFIED":         "BOT_WALLET_NOT_VERIFIED",
}


def check_live_wallet(checker: LiveWalletChecker) -> ServiceResult[Account]:
    """La cuenta de la billetera si está lista; si no, el error con código BOT_WALLET_*."""
    result = checker()
    if result.success:
        return result
    code = _BOT_CODES.get(result.error.code, "BOT_WALLET_UNAVAILABLE")
    return ServiceResult.fail(code=code, http_status=409)
