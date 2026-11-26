# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/domain/feature_set_entity.py
#
# Entidad de dominio: FeatureSet.
# Representa un conjunto de indicadores técnicos configurados.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional


class FeatureSet:
    """
    Entidad de dominio: FeatureSet.

    Define qué indicadores técnicos se calculan y sus parámetros.
    El campo `spec` es un dict JSON con la configuración de los indicadores.
    """

    def __init__(
        self,
        id: int,
        name: str,
        version: str,
        spec: dict[str, Any],
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.version = version
        self.spec = spec
        self.description = description
        self.created_at = created_at
