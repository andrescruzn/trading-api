# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/domain/signal_entity.py
#
# Entidad de dominio: Signal.
# Representa una señal de trading generada por un bot tras pasar
# por el Prompt Maestro del Agente (Módulo 6).
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any


class Signal:
    """
    Entidad de dominio: Signal.

    Una Signal es el resultado del análisis del Agente aplicado al
    contexto actual de mercado de un Bot. Puede ser APROBADA o
    RECHAZADA según los filtros de régimen, reglas y ratio R/R.

    Acciones válidas:
    - buy   : señal de compra
    - sell  : señal de venta
    - hold  : mantener posición (no operar)

    Campos de precio (solo presentes si action = buy | sell):
    - entry_price    : precio de entrada sugerido
    - stop_loss      : nivel de stop loss
    - take_profit    : nivel de take profit
    - position_size  : tamaño de la posición calculado (capital × risk_pct / |entry - SL|)

    Llamada a la IA (None si se rechazó antes de consultarla):
    - llm_provider   : servicio del pool que respondió (groq, gemini, ollama)
    - llm_model      : modelo que respondió
    - llm_latency_ms : duración de la consulta en ms (incluye el failover)

    Estado de aprobación:
    - approved = True  : pasó todos los filtros (régimen, reglas, R/R ≥ 2:1)
    - approved = False : fue rechazada en algún filtro

    Decisión de ejecución (decision_status), solo para BUY/SELL aprobadas
    de agentes en modo approval/auto:
    - not_required : no espera decisión (HOLD, rechazada o agente manual)
    - pending      : espera aprobación (o ejecución automática) hasta expires_at
    - executing    : alguien la aprobó y se está enviando la orden
    - executed     : la orden salió
    - rejected     : la persona la rechazó
    - expired      : nadie decidió a tiempo
    - failed       : se aprobó pero no se pudo ejecutar (decision_reason)
    """

    VALID_ACTIONS = ("buy", "sell", "hold")

    VALID_DECISION_STATUSES = (
        "not_required", "pending", "executing", "executed", "rejected", "expired", "failed",
    )
    VALID_DECISION_CHANNELS = ("app", "telegram", "auto")

    def __init__(
        self,
        id: int,
        bot_id: int,
        ts: datetime,
        action: str,
        approved: bool,
        reasons: dict[str, Any],
        confidence: Decimal | None = None,
        entry_price: Decimal | None = None,
        stop_loss: Decimal | None = None,
        take_profit: Decimal | None = None,
        position_size: Decimal | None = None,
        rr_ratio: Decimal | None = None,
        model_version: str | None = None,
        features_hash: str | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        llm_latency_ms: int | None = None,
        created_at: datetime | None = None,
        decision_status: str = "not_required",
        expires_at: datetime | None = None,
        decided_at: datetime | None = None,
        decided_by_user_id: int | None = None,
        decision_channel: str | None = None,
        decision_reason: str | None = None,
        candle_ts: datetime | None = None,
    ):
        self.id = id
        self.bot_id = bot_id
        self.ts = ts
        self.action = action
        self.approved = approved
        self.reasons = reasons
        self.confidence = confidence
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.position_size = position_size
        self.rr_ratio = rr_ratio
        self.model_version = model_version
        self.features_hash = features_hash
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.llm_latency_ms = llm_latency_ms
        self.created_at = created_at
        self.decision_status = decision_status
        self.expires_at = expires_at
        self.decided_at = decided_at
        self.decided_by_user_id = decided_by_user_id
        self.decision_channel = decision_channel
        self.decision_reason = decision_reason
        self.candle_ts = candle_ts

    # ------------------------------------------------------------------
    # Validaciones de negocio
    # ------------------------------------------------------------------

    def is_valid_action(self) -> bool:
        return self.action in self.VALID_ACTIONS

    def is_actionable(self) -> bool:
        """BUY/SELL aprobada por la IA: la única que puede convertirse en orden."""
        return self.approved and self.action in ("buy", "sell")

    def is_pending(self) -> bool:
        return self.decision_status == "pending"

    def is_expired_at(self, now: datetime) -> bool:
        return self.expires_at is not None and self.expires_at <= now

    def has_prices(self) -> bool:
        """Verifica que los precios estén completos para señales buy/sell."""
        return all(p is not None for p in (self.entry_price, self.stop_loss, self.take_profit))

    def compute_rr_ratio(self) -> Decimal | None:
        """
        Calcula el ratio Riesgo/Recompensa de la señal.

        Fórmula: (take_profit - entry) / (entry - stop_loss)

        Retorna None si los precios no están disponibles o el
        denominador es cero (evita división por cero).
        """
        if not self.has_prices():
            return None

        risk = self.entry_price - self.stop_loss
        reward = self.take_profit - self.entry_price

        if risk <= Decimal("0"):
            return None

        return (reward / risk).quantize(Decimal("0.01"))
