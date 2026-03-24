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

    Estado de aprobación:
    - approved = True  : pasó todos los filtros (régimen, reglas, R/R ≥ 2:1)
    - approved = False : fue rechazada en algún filtro
    """

    VALID_ACTIONS = ("buy", "sell", "hold")

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
        created_at: datetime | None = None,
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
        self.created_at = created_at

    # ------------------------------------------------------------------
    # Validaciones de negocio
    # ------------------------------------------------------------------

    def is_valid_action(self) -> bool:
        return self.action in self.VALID_ACTIONS

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
