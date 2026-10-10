# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/market_data.py
#
# PROPÓSITO:
# - Catálogos del Módulo 2 (Market Data): exchanges, timeframes y símbolos.
#
# NOTAS:
# - 7 exchanges, 14 timeframes y 37 símbolos. Binance: 18 cripto spot,
#   PAXG (oro tokenizado) y 12 perpetuos TradFi (metales, materias primas,
#   ETFs y acciones). Bybit: 4 cripto spot y 2 perpetuos (oro y plata).
# - Perpetuos TradFi: símbolo unificado de ccxt `XAU/USDT:USDT` (base/quote
#   :settle). Cotizan 24/7 y siguen el precio del activo real; ccxt elige
#   el mercado por el símbolo, así que se descargan con el mismo código que
#   el spot. Solo en paper: no se ejecutan en live (ver `is_perpetual`).
# - Ojo: `SPX/USDT:USDT` es la memecoin SPX6900, no el S&P 500.
# - TradingView queda como exchange (data_vendor) sin símbolos: no hay
#   proveedor que descargue sus velas. La migración m02 desactiva los
#   símbolos que se sembraron antes (y MATIC, renombrado a POL).
# - Los símbolos se enlazan al exchange por nombre, nunca por ID.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.market.infrastructure.exchange_model import ExchangeModel
from app.modules.market.infrastructure.symbol_model import SymbolModel
from app.modules.market.infrastructure.timeframe_model import TimeframeModel
from database.seeds._helpers import SeedStats, get_or_create

EXCHANGES: list[tuple[str, str]] = [
    ("Binance", "crypto_exchange"),
    ("Bybit", "crypto_exchange"),
    ("Kraken", "crypto_exchange"),
    ("Coinbase", "crypto_exchange"),
    ("Bitget", "crypto_exchange"),
    ("OKX", "crypto_exchange"),
    ("TradingView", "data_vendor"),
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
    "Binance": [
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
    "Bybit": [
        *[
            (f"{base}/USDT", base, "USDT", "crypto")
            for base in ("BTC", "ETH", "SOL", "XRP")
        ],
        *_perpetuals([("XAU", "metal"), ("XAG", "metal")]),
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
