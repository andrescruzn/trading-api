# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/market_data.py
#
# PROPÓSITO:
# - Catálogos del Módulo 2 (Market Data): exchanges, timeframes y símbolos.
#
# NOTAS:
# - 7 exchanges, 14 timeframes y 24 símbolos (crypto en Binance y Bybit;
#   metales y forex en TradingView como data vendor).
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
        (f"{base}/USDT", base, "USDT", "crypto")
        for base in (
            "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX",
            "LINK", "DOT", "MATIC", "UNI", "ATOM", "LTC", "BCH",
        )
    ],
    "Bybit": [
        (f"{base}/USDT", base, "USDT", "crypto")
        for base in ("BTC", "ETH", "SOL", "XRP")
    ],
    "TradingView": [
        ("XAU/USD", "XAU", "USD", "metal"),
        ("XAG/USD", "XAG", "USD", "metal"),
        ("EUR/USD", "EUR", "USD", "forex"),
        ("GBP/USD", "GBP", "USD", "forex"),
        ("USD/JPY", "USD", "JPY", "forex"),
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
