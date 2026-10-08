# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/infrastructure/candle_feature_repository_impl.py
#
# Usa INSERT ... ON DUPLICATE KEY UPDATE para bulk upsert eficiente.
# UNIQUE KEY: (symbol_id, timeframe_id, ts, feature_set_id)
# ======================================================================

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.features.domain.candle_feature_entity import CandleFeature
from app.modules.features.domain.candle_feature_repository import CandleFeatureRepository
from app.modules.features.infrastructure.candle_feature_model import CandleFeatureModel
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository


class SqlAlchemyCandleFeatureRepository(SqlAlchemyRepository, CandleFeatureRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

    @staticmethod
    def _to_domain(m: CandleFeatureModel) -> CandleFeature:
        return CandleFeature(
            id=m.id,
            symbol_id=m.symbol_id,
            timeframe_id=m.timeframe_id,
            ts=SqlAlchemyCandleFeatureRepository._as_utc(m.ts),  # type: ignore[arg-type]
            feature_set_id=m.feature_set_id,
            features=m.features or {},
            created_at=SqlAlchemyCandleFeatureRepository._as_utc(m.created_at),
        )

    def list_features(
        self,
        symbol_id: int,
        timeframe_id: int,
        feature_set_id: Optional[int] = None,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
        limit: int = 500,
    ) -> list[CandleFeature]:
        query = self._session.query(CandleFeatureModel).filter(
            CandleFeatureModel.symbol_id == symbol_id,
            CandleFeatureModel.timeframe_id == timeframe_id,
        )
        if feature_set_id is not None:
            query = query.filter(CandleFeatureModel.feature_set_id == feature_set_id)
        if from_ts is not None:
            query = query.filter(CandleFeatureModel.ts >= from_ts)
        if to_ts is not None:
            query = query.filter(CandleFeatureModel.ts <= to_ts)

        query = query.order_by(CandleFeatureModel.ts.desc()).limit(min(max(1, limit), 1000))
        return [self._to_domain(m) for m in query.all()]

    def bulk_upsert(self, features: list[CandleFeature]) -> int:
        if not features:
            return 0

        rows = []
        for f in features:
            ts_naive = f.ts.replace(tzinfo=None) if f.ts.tzinfo else f.ts
            rows.append({
                "symbol_id": f.symbol_id,
                "timeframe_id": f.timeframe_id,
                "ts": ts_naive,
                "feature_set_id": f.feature_set_id,
                "features": json.dumps(f.features),
            })

        stmt = text(
            """
            INSERT INTO candle_features
                (symbol_id, timeframe_id, ts, feature_set_id, features)
            VALUES
                (:symbol_id, :timeframe_id, :ts, :feature_set_id, :features)
            ON DUPLICATE KEY UPDATE
                features = VALUES(features)
            """
        )
        result = self._session.execute(stmt, rows)
        return result.rowcount

    def delete_beyond_retention(
        self,
        symbol_id: int,
        timeframe_id: int,
        feature_set_id: int,
        retention: int,
    ) -> int:
        # Mismo criterio que SqlAlchemyCandleRepository.delete_beyond_retention.
        result = self._session.execute(
            text("""
                DELETE FROM candle_features
                WHERE symbol_id = :sid
                  AND timeframe_id = :tid
                  AND feature_set_id = :fsid
                  AND ts < (
                      SELECT ts FROM (
                          SELECT ts FROM candle_features
                          WHERE symbol_id = :sid
                            AND timeframe_id = :tid
                            AND feature_set_id = :fsid
                          ORDER BY ts DESC
                          LIMIT 1 OFFSET :offset
                      ) AS _cutoff
                  )
            """),
            {
                "sid": symbol_id,
                "tid": timeframe_id,
                "fsid": feature_set_id,
                "offset": retention - 1,
            },
        )
        return result.rowcount
