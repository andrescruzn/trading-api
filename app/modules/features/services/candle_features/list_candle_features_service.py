# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.common.contracts import ServiceResult
from app.modules.features.domain.candle_feature_entity import CandleFeature
from app.modules.features.domain.candle_feature_repository import CandleFeatureRepository
from app.modules.features.domain.feature_set_repository import FeatureSetRepository
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository


class ListCandleFeaturesService:

    def __init__(
        self,
        candle_feature_repo: CandleFeatureRepository,
        feature_set_repo: FeatureSetRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
    ):
        self._candle_feature_repo = candle_feature_repo
        self._feature_set_repo = feature_set_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo

    def list(
        self,
        symbol_id: int,
        timeframe_id: int,
        feature_set_id: int,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
        limit: int = 500,
    ) -> ServiceResult[list[CandleFeature]]:
        if self._symbol_repo.get_by_id(symbol_id) is None:
            return ServiceResult.fail(code="SYMBOL_NOT_FOUND", http_status=404)

        if self._timeframe_repo.get_by_id(timeframe_id) is None:
            return ServiceResult.fail(code="TIMEFRAME_NOT_FOUND", http_status=404)

        if self._feature_set_repo.get_by_id(feature_set_id) is None:
            return ServiceResult.fail(code="FEATURE_SET_NOT_FOUND", http_status=404)

        features = self._candle_feature_repo.list_features(
            symbol_id=symbol_id,
            timeframe_id=timeframe_id,
            feature_set_id=feature_set_id,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=limit,
        )
        return ServiceResult.ok(data=features)
