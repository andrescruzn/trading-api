# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/infrastructure/feature_set_repository_impl.py
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.features.domain.feature_set_entity import FeatureSet
from app.modules.features.domain.feature_set_repository import FeatureSetRepository
from app.modules.features.infrastructure.feature_set_model import FeatureSetModel


class SqlAlchemyFeatureSetRepository(FeatureSetRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

    @staticmethod
    def _to_domain(m: FeatureSetModel) -> FeatureSet:
        return FeatureSet(
            id=m.id,
            name=m.name,
            version=m.version,
            spec=m.spec or {},
            description=m.description,
            created_at=SqlAlchemyFeatureSetRepository._as_utc(m.created_at),
        )

    def list_all(self) -> list[FeatureSet]:
        rows = self._session.query(FeatureSetModel).order_by(FeatureSetModel.name).all()
        return [self._to_domain(r) for r in rows]

    def get_by_id(self, feature_set_id: int) -> Optional[FeatureSet]:
        m = self._session.query(FeatureSetModel).filter_by(id=feature_set_id).first()
        return self._to_domain(m) if m else None

    def get_by_name_version(self, name: str, version: str) -> Optional[FeatureSet]:
        m = (
            self._session.query(FeatureSetModel)
            .filter_by(name=name, version=version)
            .first()
        )
        return self._to_domain(m) if m else None

    def create(self, feature_set: FeatureSet) -> FeatureSet:
        m = FeatureSetModel(
            name=feature_set.name,
            version=feature_set.version,
            description=feature_set.description,
            spec=feature_set.spec,
        )
        self._session.add(m)
        self._session.flush()
        return self._to_domain(m)
