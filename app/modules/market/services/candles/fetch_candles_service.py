# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import ccxt

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.market.domain.candle_entity import Candle
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.market.domain.exchange_repository import ExchangeRepository
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository


# Exchanges que soporta ccxt (nombre DB → id ccxt)
_CCXT_EXCHANGE_MAP: dict[str, str] = {
    "binance": "binance",
    "bybit": "bybit",
    "kraken": "kraken",
    "coinbase": "coinbase",
    "bitget": "bitget",
    "okx": "okx",
}


class FetchCandlesService:
    """
    Descarga velas OHLCV desde un exchange real via ccxt
    y las almacena en la BD usando bulk_upsert.

    El exchange se resuelve desde el símbolo (symbol.exchange_id).
    """

    def __init__(
        self,
        candle_repo: CandleRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
        exchange_repo: ExchangeRepository,
        session: Session,
    ):
        self._candle_repo = candle_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._exchange_repo = exchange_repo
        self._session = session

    def fetch(
        self,
        symbol_id: int,
        timeframe_id: int,
        limit: int = 500,
    ) -> ServiceResult[dict]:
        # 1) Validar símbolo
        symbol = self._symbol_repo.get_by_id(symbol_id)
        if symbol is None:
            return ServiceResult.fail(code="SYMBOL_NOT_FOUND", http_status=404)

        # 2) Validar timeframe
        tf = self._timeframe_repo.get_by_id(timeframe_id)
        if tf is None:
            return ServiceResult.fail(code="TIMEFRAME_NOT_FOUND", http_status=404)

        # 3) Resolver exchange
        exchange_entity = self._exchange_repo.get_by_id(symbol.exchange_id)
        if exchange_entity is None:
            return ServiceResult.fail(code="EXCHANGE_NOT_FOUND", http_status=404)

        ccxt_id = _CCXT_EXCHANGE_MAP.get(exchange_entity.name.lower())
        if ccxt_id is None:
            return ServiceResult.fail(
                code="EXCHANGE_NOT_SUPPORTED_CCXT",
                http_status=422,
                meta={"exchange": exchange_entity.name},
            )

        # 4) Descargar velas de ccxt
        try:
            exchange_cls = getattr(ccxt, ccxt_id)
            client = exchange_cls({"enableRateLimit": True})
            raw: list[list] = client.fetch_ohlcv(
                symbol.symbol,
                timeframe=tf.code,
                limit=limit,
            )
        except ccxt.BadSymbol:
            return ServiceResult.fail(
                code="CCXT_SYMBOL_NOT_FOUND",
                http_status=422,
                meta={"symbol": symbol.symbol},
            )
        except ccxt.NetworkError as e:
            return ServiceResult.fail(
                code="CCXT_NETWORK_ERROR",
                http_status=503,
                meta={"detail": str(e)[:200]},
            )
        except Exception as e:
            return ServiceResult.fail(
                code="CCXT_FETCH_ERROR",
                http_status=502,
                meta={"detail": str(e)[:200]},
            )

        if not raw:
            return ServiceResult.fail(code="CANDLES_EMPTY_PAYLOAD", http_status=422)

        # 5) Convertir a entidades Candle
        # ccxt devuelve: [timestamp_ms, open, high, low, close, volume]
        candles: list[Candle] = []
        for row in raw:
            ts = datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc)
            candle = Candle(
                id=0,
                symbol_id=symbol_id,
                timeframe_id=timeframe_id,
                ts=ts,
                open=Decimal(str(row[1])),
                high=Decimal(str(row[2])),
                low=Decimal(str(row[3])),
                close=Decimal(str(row[4])),
                volume=Decimal(str(row[5])) if row[5] is not None else Decimal("0"),
            )
            if candle.is_valid_ohlcv():
                candles.append(candle)

        if not candles:
            return ServiceResult.fail(code="CANDLES_EMPTY_PAYLOAD", http_status=422)

        # 6) Persistir
        rows_affected = self._candle_repo.bulk_upsert(candles)
        self._session.commit()

        return ServiceResult.ok(data={
            "exchange": exchange_entity.name,
            "symbol": symbol.symbol,
            "timeframe": tf.code,
            "rows_fetched": len(candles),
            "rows_affected": rows_affected,
        })
