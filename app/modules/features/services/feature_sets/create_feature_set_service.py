# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from app.common.contracts import ServiceResult
from app.modules.features.domain.feature_set_entity import FeatureSet
from app.modules.features.domain.feature_set_repository import FeatureSetRepository
from app.modules.features.domain.indicator_catalog import VALID_FOCUS, invalid_groups


class CreateFeatureSetService:

    def __init__(self, repo: FeatureSetRepository):
        self._repo = repo

    def create(
        self,
        name: str,
        version: str,
        spec: dict[str, Any],
        description: str | None = None,
    ) -> ServiceResult[FeatureSet]:
        # El spec solo puede pedir grupos que el cálculo sabe producir
        invalid = invalid_groups(spec)
        if invalid:
            return ServiceResult.fail(
                code="FEATURE_SET_INVALID_INDICATORS",
                http_status=422,
                meta={"invalid": invalid},
            )
        if "focus" in spec and spec["focus"] not in VALID_FOCUS:
            return ServiceResult.fail(code="FEATURE_SET_INVALID_FOCUS", http_status=422)

        # Verificar que no exista ya un feature set con el mismo nombre y versión
        existing = self._repo.get_by_name_version(name=name, version=version)
        if existing:
            return ServiceResult.fail(
                code="FEATURE_SET_ALREADY_EXISTS",
                http_status=409,
            )

        feature_set = FeatureSet(
            id=0,
            name=name,
            version=version,
            spec=spec,
            description=description,
        )
        created = self._repo.create(feature_set)
        self._repo.commit()
        return ServiceResult.ok(data=created)
