# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/market_data.py
#
# PROPÓSITO:
# - Catálogos del Módulo 2 (Market Data): exchanges, timeframes y símbolos.
#
# NOTAS:
# - 1 exchange (Binance, el único de la plataforma), 14 timeframes y 31
#   símbolos: 18 cripto spot, PAXG (oro tokenizado) y 12 perpetuos TradFi
#   (metales, materias primas, ETFs y acciones).
# - Perpetuos TradFi: símbolo unificado de ccxt `XAU/USDT:USDT` (base/quote
#   :settle). Cotizan 24/7 y siguen el precio del activo real; ccxt elige
#   el mercado por el símbolo, así que se descargan con el mismo código que
#   el spot. Solo en paper: no se ejecutan en live (ver `is_perpetual`).
# - Ojo: `SPX/USDT:USDT` es la memecoin SPX6900, no el S&P 500.
# - Los exchanges que se sembraban antes (Bybit, Kraken, Coinbase,
#   Bitget, OKX, TradingView) los desactiva la migración "m02 solo
#   binance" junto con sus símbolos.
# - Los símbolos se enlazan al exchange por nombre, nunca por ID.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.market.domain.ccxt_exchanges import PLATFORM_EXCHANGE_NAME
from app.modules.market.infrastructure.exchange_model import ExchangeModel
from app.modules.market.infrastructure.symbol_model import SymbolModel
from app.modules.market.infrastructure.timeframe_model import TimeframeModel
from database.seeds._helpers import SeedStats, get_or_create

EXCHANGES: list[tuple[str, str]] = [
    (PLATFORM_EXCHANGE_NAME, "crypto_exchange"),
]


def _perpetuals(items: list[tuple[str, str]]) -> list[tuple[str, str, str, str]]:
    """Perpetuos lineales en USDT: `XAU` → `XAU/USDT:USDT`."""
    return [(f"{base}/USDT:USDT", base, "USDT", asset_class) for base, asset_class in items]


TIMEFRAMES: list[tuple[str, int]] = [
    ("1m", 60),
    ("3m", 180),
    ("5m", 300),
    ("15m", 900),
    ("30m", 1800),
    ("1h", 3600),
    ("2h", 7200),
    ("4h", 14400),
    ("6h", 21600),
    ("8h", 28800),
    ("12h", 43200),
    ("1d", 86400),
    ("3d", 259200),
    ("1w", 604800),
]

# exchange → [(symbol, base, quote, asset_class)]
SYMBOLS: dict[str, list[tuple[str, str, str, str]]] = {
    PLATFORM_EXCHANGE_NAME: [
        *[
            (f"{base}/USDT", base, "USDT", "crypto")
            for base in (
                "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX",
                "LINK", "DOT", "POL", "UNI", "ATOM", "LTC", "BCH",
                "TRX", "NEAR", "SUI",
            )
        ],
        # Token respaldado por oro físico: el único "oro" en spot (long-only)
        ("PAXG/USDT", "PAXG", "USDT", "metal"),
        *_perpetuals(
            [
                ("XAU", "metal"),       # oro
                ("XAG", "metal"),       # plata
                ("XPT", "metal"),       # platino
                ("XPD", "metal"),       # paladio
                ("CL", "commodity"),    # petróleo WTI
                ("NATGAS", "commodity"),
                ("COPPER", "commodity"),
                ("SPY", "etf"),         # S&P 500
                ("QQQ", "etf"),         # Nasdaq 100
                ("NVDA", "stock"),
                ("TSLA", "stock"),
                ("AAPL", "stock"),
            ]
        ),
    ],
}


def run(session: Session) -> SeedStats:
    stats = SeedStats()

    exchanges: dict[str, ExchangeModel] = {}
    for name, type_ in EXCHANGES:
        exchanges[name] = get_or_create(
            session,
            ExchangeModel,
            lookup={"name": name},
            values={"type": type_, "is_active": True},
            stats=stats,
        )

    for code, seconds in TIMEFRAMES:
        get_or_create(
            session,
            TimeframeModel,
            lookup={"code": code},
            values={"seconds": seconds},
            stats=stats,
        )

    for exchange_name, symbols in SYMBOLS.items():
        exchange_id = exchanges[exchange_name].id
        for symbol, base, quote, asset_class in symbols:
            get_or_create(
                session,
                SymbolModel,
                lookup={"exchange_id": exchange_id, "symbol": symbol},
                values={
                    "base_asset": base,
                    "quote_asset": quote,
                    "asset_class": asset_class,
                    "is_active": True,
                },
                stats=stats,
            )

    return stats
