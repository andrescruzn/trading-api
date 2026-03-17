# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/domain/ml_model_entity.py
#
# Entidad de dominio: MLModel.
# Representa un modelo de Machine Learning registrado en el sistema.
#
# NOTA: Se llama MLModel (no Model) para evitar colisión con la palabra
#       reservada de SQLAlchemy y con los patrones de nomenclatura ORM.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any


class MLModel:
    """
    Entidad de dominio: MLModel.

    Representa un modelo entrenado de ML que el agente puede usar para
    generar predicciones (xgboost, lightgbm, sklearn, nn).

    Estados válidos:
    - active     : modelo en producción (usado para predicciones)
    - deprecated : fue reemplazado por una versión más nueva
    - archived   : desactivado, ya no se usa
    """

    VALID_TYPES = ("xgboost", "lightgbm", "sklearn", "nn")
    VALID_STATUSES = ("active", "deprecated", "archived")

    def __init__(
        self,
        id: int,
        name: str,
        version: str,
        model_type: str,
        meta: dict[str, Any],
        feature_set_id: int | None = None,
        artifact_uri: str | None = None,
        status: str = "active",
        created_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.version = version
        self.model_type = model_type
        self.feature_set_id = feature_set_id
        self.artifact_uri = artifact_uri
        self.status = status
        self.meta = meta
        self.created_at = created_at

    # ------------------------------------------------------------------
    # Validaciones de negocio
    # ------------------------------------------------------------------

    def is_valid_type(self) -> bool:
        return self.model_type in self.VALID_TYPES

    def is_valid_status(self) -> bool:
        return self.status in self.VALID_STATUSES

    def is_active(self) -> bool:
        return self.status == "active"
