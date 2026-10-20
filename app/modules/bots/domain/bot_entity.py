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

    # Qué pasa cuando la IA aprueba una operación:
    # - manual   : solo señales con "Analizar ahora"; la orden la crea la persona
    # - approval : señales automáticas por vela; la orden espera aprobación humana
    # - auto     : señales automáticas por vela; la orden sale sola
    VALID_EXECUTION_MODES = ("manual", "approval", "auto")
    AUTOMATED_EXECUTION_MODES = ("approval", "auto")

    # Regla del 1 %: nunca arriesgar más del 1 % del capital por operación
    MAX_RISK_PCT = 0.01

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
        name: str,
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
        execution_mode: str = "manual",
        approval_ttl_minutes: int | None = None,
        share_signals: bool = False,
    ):
        self.id = id
        self.name = name
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
        self.execution_mode = execution_mode
        self.approval_ttl_minutes = approval_ttl_minutes
        # Otros usuarios pueden suscribirse a sus señales aprobadas (Telegram)
        self.share_signals = share_signals

    # ------------------------------------------------------------------
    # Accessors sobre risk_params
    # ------------------------------------------------------------------

    @property
    def risk_pct(self) -> float:
        """Porcentaje del capital a arriesgar por operación (ej: 0.01 = 1%)."""
        return float(self.risk_params.get("risk_pct", 0.01))

    @property
    def effective_risk_pct(self) -> float:
        """risk_pct acotado por la Regla del 1 % (nunca más de MAX_RISK_PCT)."""
        return min(self.risk_pct, self.MAX_RISK_PCT) if self.risk_pct > 0 else self.MAX_RISK_PCT

    @property
    def max_drawdown_pct(self) -> float | None:
        """Máximo drawdown permitido antes de detener el bot automáticamente."""
        val = self.risk_params.get("max_drawdown_pct")
        return float(val) if val is not None else None

    @property
    def max_notional(self) -> float | None:
        """Valor máximo (qty × precio) por orden que fija el bot, si lo fija."""
        val = self.risk_params.get("max_notional")
        try:
            return float(val) if val is not None and float(val) > 0 else None
        except (TypeError, ValueError):
            return None

    # ------------------------------------------------------------------
    # Validaciones de negocio
    # ------------------------------------------------------------------

    def is_valid_status(self) -> bool:
        return self.status in self.VALID_STATUSES

    def is_valid_mode(self) -> bool:
        return self.mode in self.VALID_MODES

    def is_valid_execution_mode(self) -> bool:
        return self.execution_mode in self.VALID_EXECUTION_MODES

    def is_automated(self) -> bool:
        """True si el scheduler genera sus señales en cada vela cerrada."""
        return self.execution_mode in self.AUTOMATED_EXECUTION_MODES

    @classmethod
    def is_valid_risk_pct(cls, value: object) -> bool:
        """risk_pct debe estar en (0, MAX_RISK_PCT] (fracción: 0.01 = 1 %)."""
        try:
            return 0 < float(value) <= cls.MAX_RISK_PCT  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False

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
