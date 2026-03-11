# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/domain/feature_set_repository.py
#
# Contrato (interfaz) del repositorio de FeatureSets.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.features.domain.feature_set_entity import FeatureSet


class FeatureSetRepository(ABC):

    @abstractmethod
    def list_all(self) -> list[FeatureSet]: ...

    @abstractmethod
    def get_by_id(self, feature_set_id: int) -> Optional[FeatureSet]: ...

    @abstractmethod
    def get_by_name_version(self, name: str, version: str) -> Optional[FeatureSet]: ...

    @abstractmethod
    def create(self, feature_set: FeatureSet) -> FeatureSet: ...
