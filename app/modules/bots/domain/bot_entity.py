# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/domain/bot_entity.py
#
# Entidad de dominio: Bot.
# Representa un bot de trading activo que combina una cuenta, símbolo,
# estrategia y timeframe para generar señales automáticas.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any


class Bot:
    """
    Entidad de dominio: Bot.

    Un Bot instancia una estrategia de trading sobre un símbolo y
    timeframe específicos, operando sobre una cuenta del usuario.

    Estados válidos:
    - stopped  : bot detenido (estado inicial)
    - running  : bot activo, generando señales
    - paused   : bot pausado temporalmente (conserva configuración)
    - error    : bot detenido por error interno

    Transiciones de estado permitidas:
    - stopped  → running
    - running  → paused, stopped, error
    - paused   → running, stopped
    - error    → stopped
    """

    VALID_STATUSES = ("running", "stopped", "paused", "error")
    VALID_MODES = ("paper", "live")

    # Mapa de transiciones válidas: estado_actual → estados_permitidos
    _ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
        "stopped": ("running",),
        "running": ("paused", "stopped", "error"),
        "paused":  ("running", "stopped"),
        "error":   ("stopped",),
    }

    def __init__(
        self,
        id: int,
        strategy_id: int,
        symbol_id: int,
        timeframe_id: int,
        account_id: int,
        feature_set_id: int,
        mode: str,
        status: str,
        risk_params: dict[str, Any],
        started_at: datetime | None = None,
        stopped_at: datetime | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.strategy_id = strategy_id
        self.symbol_id = symbol_id
        self.timeframe_id = timeframe_id
        self.account_id = account_id
        self.feature_set_id = feature_set_id
        self.mode = mode
        self.status = status
        self.risk_params = risk_params
        self.started_at = started_at
        self.stopped_at = stopped_at
        self.created_at = created_at

    # ------------------------------------------------------------------
    # Accessors sobre risk_params
    # ------------------------------------------------------------------

    @property
    def risk_pct(self) -> float:
        """Porcentaje del capital a arriesgar por operación (ej: 0.01 = 1%)."""
        return float(self.risk_params.get("risk_pct", 0.01))

    @property
    def max_drawdown_pct(self) -> float | None:
        """Máximo drawdown permitido antes de detener el bot automáticamente."""
        val = self.risk_params.get("max_drawdown_pct")
        return float(val) if val is not None else None

    # ------------------------------------------------------------------
    # Validaciones de negocio
    # ------------------------------------------------------------------

    def is_valid_status(self) -> bool:
        return self.status in self.VALID_STATUSES

    def is_valid_mode(self) -> bool:
        return self.mode in self.VALID_MODES

    def can_transition_to(self, new_status: str) -> bool:
        """
        Verifica si la transición de estado es válida.

        Regla de negocio: no se puede cambiar al mismo estado ni
        saltar entre estados no adyacentes (ej: error → running).
        """
        if self.status == new_status:
            return False
        allowed = self._ALLOWED_TRANSITIONS.get(self.status, ())
        return new_status in allowed

    def is_active(self) -> bool:
        """Un bot es activo si está corriendo o pausado."""
        return self.status in ("running", "paused")
