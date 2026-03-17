# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.agent.domain.ml_model_entity import MLModel
from app.modules.agent.domain.ml_model_repository import MLModelRepository


class CreateModelService:
    """
    Registra un nuevo modelo ML en el sistema.

    Reglas de negocio:
    - name + version deben ser únicos.
    - model_type debe ser uno de: xgboost, lightgbm, sklearn, nn.
    """

    def __init__(self, repo: MLModelRepository, session: Session):
        self._repo = repo
        self._session = session

    def create(
        self,
        name: str,
        version: str,
        model_type: str,
        meta: dict[str, Any],
        feature_set_id: Optional[int] = None,
        artifact_uri: Optional[str] = None,
    ) -> ServiceResult[MLModel]:
        # Validar tipo
        if model_type not in MLModel.VALID_TYPES:
            return ServiceResult.fail(code="MODEL_INVALID_TYPE", http_status=422)

        # Verificar duplicado
        existing = self._repo.get_by_name_version(name, version)
        if existing is not None:
            return ServiceResult.fail(
                code="MODEL_DUPLICATE_NAME_VERSION", http_status=409
            )

        model = MLModel(
            id=0,
            name=name.strip(),
            version=version.strip(),
            model_type=model_type,
            feature_set_id=feature_set_id,
            artifact_uri=artifact_uri,
            status="active",
            meta=meta,
        )

        created = self._repo.create(model)
        self._session.commit()
        return ServiceResult.ok(data=created)
