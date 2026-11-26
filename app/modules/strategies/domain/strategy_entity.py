# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/domain/strategy_entity.py
#
# Entidad de dominio: Strategy.
# Representa una estrategia de trading con sus reglas y configuración.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any


class Strategy:
    """
    Entidad de dominio: Strategy.

    Una estrategia define las reglas y condiciones bajo las cuales
    el sistema debe considerar entrar o salir de una operación.

    Tipos válidos:
    - trend_following  : opera cuando el mercado está en tendencia (HH/HL)
    - mean_reversion   : opera cuando el precio se aleja de su promedio

    Regímenes válidos:
    - trend_up    : tendencia alcista (máximos más altos)
    - trend_down  : tendencia bajista (mínimos más bajos)
    - sideways    : mercado lateral/rango

    Regla de coherencia:
    - trend_following  → regime_required debe ser trend_up o trend_down
    - mean_reversion   → regime_required debe ser sideways o None
    """

    VALID_TYPES = ("trend_following", "mean_reversion")
    VALID_REGIMES = ("trend_up", "trend_down", "sideways")

    # Coherencia: qué regímenes acepta cada tipo de estrategia
    _ALLOWED_REGIMES: dict[str, tuple[str, ...]] = {
        "trend_following": ("trend_up", "trend_down"),
        "mean_reversion":  ("sideways",),
    }

    def __init__(
        self,
        id: int,
        name: str,
        version: str,
        parameters: dict[str, Any],
        description: str | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.version = version
        self.description = description
        self.parameters = parameters
        self.created_at = created_at

    # ------------------------------------------------------------------
    # Accessors sobre parameters
    # ------------------------------------------------------------------

    @property
    def strategy_type(self) -> str | None:
        return self.parameters.get("strategy_type")

    @property
    def regime_required(self) -> str | None:
        return self.parameters.get("regime_required")

    @property
    def timeframe_code(self) -> str | None:
        return self.parameters.get("timeframe_code")

    @property
    def rules(self) -> list[dict[str, Any]]:
        return self.parameters.get("rules", [])

    # ------------------------------------------------------------------
    # Validaciones de negocio
    # ------------------------------------------------------------------

    def is_valid_type(self) -> bool:
        return self.strategy_type in self.VALID_TYPES

    def is_coherent(self) -> bool:
        """
        Valida que el strategy_type y el regime_required sean coherentes.

        - trend_following necesita trend_up o trend_down (no sideways)
        - mean_reversion  necesita sideways (no trend_up ni trend_down)
        - Si regime_required es None, siempre coherente
        """
        if self.regime_required is None:
            return True
        if self.strategy_type not in self._ALLOWED_REGIMES:
            return False
        return self.regime_required in self._ALLOWED_REGIMES[self.strategy_type]
