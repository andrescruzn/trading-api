# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/providers/feature_provider.py
#
# Factory que centraliza la creación de todos los servicios de features.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.features.infrastructure import (
    SqlAlchemyFeatureSetRepository,
    SqlAlchemyCandleFeatureRepository,
)
from app.modules.features.services.feature_sets import (
    ListFeatureSetsService,
    CreateFeatureSetService,
)
from app.modules.features.services.calculations import CalculateFeaturesService
from app.modules.features.services.candle_features import ListCandleFeaturesService
from app.modules.market.infrastructure import (
    SqlAlchemyCandleRepository,
    SqlAlchemySymbolRepository,
    SqlAlchemyTimeframeRepository,
)


class FeatureServiceFactory:
    """
    Factory para todos los servicios del módulo Feature Engineering.

    Uso en routes:
        factory = FeatureServiceFactory(session=db)
        result = factory.list_feature_sets().list()
    """

    def __init__(self, session: Session):
        self._session = session

        self._feature_set_repo = SqlAlchemyFeatureSetRepository(session)
        self._candle_feature_repo = SqlAlchemyCandleFeatureRepository(session)
        self._candle_repo = SqlAlchemyCandleRepository(session)
        self._symbol_repo = SqlAlchemySymbolRepository(session)
        self._timeframe_repo = SqlAlchemyTimeframeRepository(session)

    def list_feature_sets(self) -> ListFeatureSetsService:
        return ListFeatureSetsService(repo=self._feature_set_repo)

    def create_feature_set(self) -> CreateFeatureSetService:
        return CreateFeatureSetService(repo=self._feature_set_repo, session=self._session)

    def calculate_features(self) -> CalculateFeaturesService:
        return CalculateFeaturesService(
            candle_repo=self._candle_repo,
            feature_set_repo=self._feature_set_repo,
            candle_feature_repo=self._candle_feature_repo,
            symbol_repo=self._symbol_repo,
            timeframe_repo=self._timeframe_repo,
            session=self._session,
        )

    def list_candle_features(self) -> ListCandleFeaturesService:
        return ListCandleFeaturesService(
            candle_feature_repo=self._candle_feature_repo,
            feature_set_repo=self._feature_set_repo,
            symbol_repo=self._symbol_repo,
            timeframe_repo=self._timeframe_repo,
        )


def get_feature_factory(session: Session) -> FeatureServiceFactory:
    return FeatureServiceFactory(session=session)
