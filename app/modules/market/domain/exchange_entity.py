# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/domain/exchange_entity.py
#
# Entidad de dominio: Exchange
# Sin ORM, sin FastAPI. Solo lógica pura de negocio.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Optional


class Exchange:
    """
    Entidad de dominio: Exchange (exchange/broker/data_vendor).

    Responsabilidad:
    - Modelar un exchange y su estado activo/inactivo.
    - Tipos válidos: crypto_exchange | broker | data_vendor
    """

    VALID_TYPES = ("crypto_exchange", "broker", "data_vendor")

    def __init__(
        self,
        id: int,
        name: str,
        type: str,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.type = type
        self.is_active = is_active
        self.created_at = created_at

    def activate(self) -> None:
        """Activa el exchange."""
        self.is_active = True

    def deactivate(self) -> None:
        """Desactiva el exchange (no se puede usar para símbolos nuevos)."""
        self.is_active = False

    def is_valid_type(self) -> bool:
        """Verifica que el tipo es uno de los valores permitidos."""
        return self.type in self.VALID_TYPES
