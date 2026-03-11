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
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
import pandas_ta as ta
from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.features.domain.candle_feature_entity import CandleFeature
from app.modules.features.domain.candle_feature_repository import CandleFeatureRepository
from app.modules.features.domain.feature_set_repository import FeatureSetRepository
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository

# Número mínimo de velas para calcular EMA(200) con margen
_MIN_CANDLES = 220


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
        session: Session,
    ):
        self._candle_repo = candle_repo
        self._feature_set_repo = feature_set_repo
        self._candle_feature_repo = candle_feature_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._session = session

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

        if self._feature_set_repo.get_by_id(feature_set_id) is None:
            return ServiceResult.fail(code="FEATURE_SET_NOT_FOUND", http_status=404)

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

        if len(candles) < _MIN_CANDLES:
            return ServiceResult.fail(
                code="INSUFFICIENT_CANDLES",
                http_status=422,
                meta={"required": _MIN_CANDLES, "available": len(candles)},
            )

        # ------------------------------------------------------------------
        # 3. Construir DataFrame
        # ------------------------------------------------------------------
        df = pd.DataFrame([{
            "ts": c.ts,
            "open": float(c.open),
            "high": float(c.high),
            "low": float(c.low),
            "close": float(c.close),
            "volume": float(c.volume),
        } for c in candles])
        df.set_index("ts", inplace=True)

        # ------------------------------------------------------------------
        # 4. Calcular indicadores con pandas-ta
        # ------------------------------------------------------------------
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.atr(length=14, append=True)
        df.ta.bbands(length=20, std=2, append=True)

        # Volumen relativo: vol / media_móvil_vol_20
        df["vol_rel"] = df["volume"] / df["volume"].rolling(20).mean()

        # ------------------------------------------------------------------
        # 5. Detectar régimen de mercado
        # ------------------------------------------------------------------
        df["regime"] = df.apply(
            lambda row: self._detect_regime(df, row.name), axis=1
        )

        # ------------------------------------------------------------------
        # 6. Construir entidades CandleFeature (solo filas con datos completos)
        # ------------------------------------------------------------------
        # Columnas que deben existir sin NaN para considerar la fila válida
        required_cols = ["RSI_14", "EMA_20", "EMA_50", "EMA_200", "ATRr_14"]
        df_valid = df.dropna(subset=required_cols)

        feature_entities = []
        for ts, row in df_valid.iterrows():
            features = {
                "rsi_14":        self._safe_float(row.get("RSI_14")),
                "ema_20":        self._safe_float(row.get("EMA_20")),
                "ema_50":        self._safe_float(row.get("EMA_50")),
                "ema_200":       self._safe_float(row.get("EMA_200")),
                "macd":          self._safe_float(row.get("MACD_12_26_9")),
                "macd_signal":   self._safe_float(row.get("MACDs_12_26_9")),
                "macd_hist":     self._safe_float(row.get("MACDh_12_26_9")),
                "atr_14":        self._safe_float(row.get("ATRr_14")),
                "bb_upper":      self._safe_float(row.get("BBU_20_2.0_2.0")),
                "bb_mid":        self._safe_float(row.get("BBM_20_2.0_2.0")),
                "bb_lower":      self._safe_float(row.get("BBL_20_2.0_2.0")),
                "bb_bandwidth":  self._safe_float(row.get("BBB_20_2.0_2.0")),
                "vol_rel":       self._safe_float(row.get("vol_rel")),
                "regime":        row.get("regime", "sideways"),
            }
            feature_entities.append(CandleFeature(
                id=0,
                symbol_id=symbol_id,
                timeframe_id=timeframe_id,
                ts=ts,
                feature_set_id=feature_set_id,
                features=features,
            ))

        # ------------------------------------------------------------------
        # 7. Persistir
        # ------------------------------------------------------------------
        rows_affected = self._candle_feature_repo.bulk_upsert(feature_entities)
        self._session.commit()

        return ServiceResult.ok(data={
            "symbol_id": symbol_id,
            "timeframe_id": timeframe_id,
            "feature_set_id": feature_set_id,
            "candles_loaded": len(candles),
            "rows_calculated": len(feature_entities),
            "rows_affected": rows_affected,
        })

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Convierte a float; retorna None si es NaN o None."""
        try:
            import math
            v = float(value)
            return None if math.isnan(v) else round(v, 8)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _detect_regime(df: pd.DataFrame, current_ts) -> str:
        """
        Detecta régimen de mercado usando lógica HH/HL (Higher Highs / Higher Lows).

        Reglas (ventana de 20 velas):
        - trend_up:   los últimos 2 máximos son ascendentes Y los últimos 2 mínimos son ascendentes
        - trend_down: los últimos 2 máximos son descendentes Y los últimos 2 mínimos son descendentes
        - sideways:   cualquier otro caso
        """
        try:
            idx = df.index.get_loc(current_ts)
            if idx < 20:
                return "sideways"

            window = df.iloc[idx - 20: idx]
            highs = window["high"].values
            lows = window["low"].values

            # Detectar swing highs y swing lows locales (ventana de 3)
            swing_highs = [
                highs[i] for i in range(1, len(highs) - 1)
                if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]
            ]
            swing_lows = [
                lows[i] for i in range(1, len(lows) - 1)
                if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]
            ]

            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                hh = swing_highs[-1] > swing_highs[-2]
                hl = swing_lows[-1] > swing_lows[-2]
                lh = swing_highs[-1] < swing_highs[-2]
                ll = swing_lows[-1] < swing_lows[-2]

                if hh and hl:
                    return "trend_up"
                if lh and ll:
                    return "trend_down"

            return "sideways"
        except Exception:
            return "sideways"
