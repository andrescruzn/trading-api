# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/domain/ccxt_exchanges.py
#
# PROPÓSITO:
# - Exchanges de los que el sistema sabe descargar velas solo (ccxt).
#   Lo usan la descarga de velas y la respuesta de símbolos
#   (`supports_auto_fetch`), para que la UI no ofrezca crear agentes
#   sobre símbolos que nunca recibirían datos.
# - Distinguir perpetuos (`XAU/USDT:USDT`) de spot: los perpetuos TradFi
#   se descargan y se operan en paper, pero no en live.
#
# NOTAS:
# - Dominio puro: solo nombres, sin importar ccxt.
# ======================================================================

from __future__ import annotations

# Exchanges que soporta ccxt (nombre DB en minúsculas → id ccxt)
CCXT_EXCHANGE_MAP: dict[str, str] = {
    "binance": "binance",
    "bybit": "bybit",
    "kraken": "kraken",
    "coinbase": "coinbase",
    "bitget": "bitget",
    "okx": "okx",
}


def ccxt_id_for(exchange_name: str | None) -> str | None:
    """Id ccxt del exchange, o None si no se descarga automáticamente."""
    if not exchange_name:
        return None
    return CCXT_EXCHANGE_MAP.get(exchange_name.lower())


def supports_auto_fetch(exchange_name: str | None) -> bool:
    """True si las velas de ese exchange se descargan solas (scheduler)."""
    return ccxt_id_for(exchange_name) is not None


def is_perpetual(symbol: str | None) -> bool:
    """
    True si el símbolo unificado de ccxt es un contrato (`BASE/QUOTE:SETTLE`).

    En live un contrato se opera en número de contratos, con apalancamiento
    y posiciones cortas; la ejecución live solo sabe de spot long-only, así
    que estos símbolos quedan restringidos a paper.
    """
    return bool(symbol) and ":" in symbol
