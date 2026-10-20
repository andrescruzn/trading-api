# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/services/calculations/calculate_features_service.py
#
# Calcula indicadores técnicos sobre velas OHLCV y detecta el régimen
# de mercado. Usa pandas-ta para los indicadores estándar.
#
# Indicadores calculados:
#   - RSI(14)
#   - EMA(20), EMA(50), EMA(200)
#   - MACD(12, 26, 9)
#   - ATR(14)
#   - Bollinger Bands(20, 2)
#   - Volumen relativo (vol / media_vol_20)
#   - Régimen: trend_up | trend_down | sideways
#
# Solo se guardan los indicadores de los grupos del `spec` del feature
# set (ver `indicator_catalog`); el régimen se guarda siempre.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.common.contracts import ServiceResult
from app.modules.features.domain.candle_feature_entity import CandleFeature
from app.modules.features.domain.candle_feature_repository import CandleFeatureRepository
from app.modules.features.domain.feature_set_repository import FeatureSetRepository
from app.modules.features.domain.indicator_catalog import groups_for
from app.modules.features.domain.indicator_engine import MIN_CANDLES, compute_feature_rows
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository


class CalculateFeaturesService:
    """
    Calcula indicadores técnicos para un rango de velas y los persiste
    en `candle_features`.

    Flujo:
    1. Valida symbol, timeframe y feature_set.
    2. Carga velas (necesita al menos 220 para EMA200 fiable).
    3. Calcula todos los indicadores con pandas-ta.
    4. Detecta régimen de mercado (HH/HL vs lateral).
    5. Persiste en bulk_upsert.
    """

    def __init__(
        self,
        candle_repo: CandleRepository,
        feature_set_repo: FeatureSetRepository,
        candle_feature_repo: CandleFeatureRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
    ):
        self._candle_repo = candle_repo
        self._feature_set_repo = feature_set_repo
        self._candle_feature_repo = candle_feature_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo

    def calculate(
        self,
        symbol_id: int,
        timeframe_id: int,
        feature_set_id: int,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
    ) -> ServiceResult[dict]:
        # ------------------------------------------------------------------
        # 1. Validaciones
        # ------------------------------------------------------------------
        if self._symbol_repo.get_by_id(symbol_id) is None:
            return ServiceResult.fail(code="SYMBOL_NOT_FOUND", http_status=404)

        if self._timeframe_repo.get_by_id(timeframe_id) is None:
            return ServiceResult.fail(code="TIMEFRAME_NOT_FOUND", http_status=404)

        feature_set = self._feature_set_repo.get_by_id(feature_set_id)
        if feature_set is None:
            return ServiceResult.fail(code="FEATURE_SET_NOT_FOUND", http_status=404)

        groups = groups_for(feature_set.spec)

        # ------------------------------------------------------------------
        # 2. Cargar velas (hasta 1000, ordenadas de más antigua a más nueva)
        # ------------------------------------------------------------------
        candles = self._candle_repo.list_candles(
            symbol_id=symbol_id,
            timeframe_id=timeframe_id,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=1000,
        )
        # list_candles devuelve orden desc → invertir para cálculos cronológicos
        candles = list(reversed(candles))

        if len(candles) < MIN_CANDLES:
            return ServiceResult.fail(
                code="INSUFFICIENT_CANDLES",
                http_status=422,
                meta={"required": MIN_CANDLES, "available": len(candles)},
            )

        # ------------------------------------------------------------------
        # 3. Indicadores + régimen (domain/indicator_engine.py)
        # ------------------------------------------------------------------
        feature_entities = [
            CandleFeature(
                id=0,
                symbol_id=symbol_id,
                timeframe_id=timeframe_id,
                ts=ts,
                feature_set_id=feature_set_id,
                features=features,
            )
            for ts, features in compute_feature_rows(candles, groups)
        ]

        # ------------------------------------------------------------------
        # 4. Persistir
        # ------------------------------------------------------------------
        rows_affected = self._candle_feature_repo.bulk_upsert(feature_entities)
        self._candle_feature_repo.commit()

        return ServiceResult.ok(data={
            "symbol_id": symbol_id,
            "timeframe_id": timeframe_id,
            "feature_set_id": feature_set_id,
            "candles_loaded": len(candles),
            "rows_calculated": len(feature_entities),
            "rows_affected": rows_affected,
        })
