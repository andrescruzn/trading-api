# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/domain/platform_wallet_rules.py
#
# REGLA (billetera lista para operar en real, 2026-11-27):
# - Un agente real solo se crea o se inicia si la billetera de Binance
#   está lista: credenciales en el `.env`, billetera creada y una
#   sincronización con Binance que confirmó que las llaves sirven.
# - Se usa lo que guardó la última sincronización (`platform_wallet`):
#   no se llama a Binance al crear ni al iniciar un agente.
# - Un fallo de red o de saldo en la última sincronización NO bloquea:
#   es pasajero y no dice nada sobre si las llaves son válidas.
# ======================================================================

from __future__ import annotations

from app.modules.accounts.domain.platform_wallet_entity import PlatformWallet

# Fallos de sincronización que sí indican llaves faltantes o rechazadas
_CREDENTIAL_SYNC_ERRORS = frozenset({"WALLET_EXCHANGE_AUTH_FAILED", "WALLET_CREDENTIALS_MISSING"})


def live_block_code(credentials_configured: bool, wallet: PlatformWallet | None) -> str | None:
    """
    Código de por qué la billetera no sirve para operar en real, o None si
    está lista. Orden: llaves → billetera → llaves rechazadas → sin verificar.
    """
    if not credentials_configured:
        return "WALLET_CREDENTIALS_MISSING"
    if wallet is None:
        return "WALLET_UNAVAILABLE"
    if wallet.last_sync_error in _CREDENTIAL_SYNC_ERRORS:
        return "WALLET_EXCHANGE_AUTH_FAILED"
    if wallet.last_synced_at is None:
        return "WALLET_NOT_VERIFIED"
    return None
