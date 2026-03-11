# -*- coding: utf-8 -*-

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.features.domain.feature_set_entity import FeatureSet
from app.modules.features.domain.feature_set_repository import FeatureSetRepository


class ListFeatureSetsService:

    def __init__(self, repo: FeatureSetRepository):
        self._repo = repo

    def list(self) -> ServiceResult[list[FeatureSet]]:
        feature_sets = self._repo.list_all()
        return ServiceResult.ok(data=feature_sets)
