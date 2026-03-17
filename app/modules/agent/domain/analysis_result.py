# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/domain/analysis_result.py
#
# Value object que encapsula el resultado completo del Prompt Maestro.
#
# El análisis pasa por 4 fases:
#   1. Filtro de Régimen → ¿el mercado coincide con lo que requiere la estrategia?
#   2. Validación de Reglas → ¿se cumplen TODAS las reglas de la estrategia?
#   3. Análisis LLM → entry / stop_loss / take_profit / reasoning
#   4. Filtro R/R → ¿la ganancia proyectada >= MIN_RR_RATIO × el riesgo?
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleCheckDetail:
    """Detalle de la evaluación de una regla individual."""

    indicator: str
    operator: str
    threshold: Any          # valor configurado en la estrategia
    actual_value: Any       # valor real del indicador en el último candle
    passed: bool


@dataclass
class AnalysisResult:
    """
    Resultado completo del Prompt Maestro.

    decision: "APPROVED" si pasó todas las fases, "REJECTED" si falló alguna.
    rejection_reason: código estable de la razón de rechazo (None si APPROVED).

    Fases que se evaluaron:
    - regime_check_passed  : bool
    - rules_check_passed   : bool
    - rr_check_passed      : bool
    """

    # ------------------------------------------------------------------
    # Decisión final
    # ------------------------------------------------------------------
    decision: str                           # "APPROVED" | "REJECTED"
    rejection_reason: str | None            # código de la razón (si REJECTED)

    # ------------------------------------------------------------------
    # Precios calculados / sugeridos por el LLM
    # ------------------------------------------------------------------
    entry: float | None                     # precio de entrada sugerido
    stop_loss: float | None                 # stop loss
    take_profit: float | None               # take profit
    position_size: float | None             # unidades a operar
    rr_ratio: float | None                  # reward/risk calculado

    # ------------------------------------------------------------------
    # Contexto del LLM
    # ------------------------------------------------------------------
    reasoning: str                          # explicación del LLM
    confidence: float | None                # 0.0 – 1.0 (si el LLM lo retorna)

    # ------------------------------------------------------------------
    # Fases de validación (para transparencia / auditoría)
    # ------------------------------------------------------------------
    regime_check_passed: bool
    rules_check_passed: bool
    rr_check_passed: bool
    rules_detail: list[RuleCheckDetail] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Snapshot de contexto (para guardar en predictions.raw_output)
    # ------------------------------------------------------------------
    meta: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def approved(self) -> bool:
        return self.decision == "APPROVED"

    def to_dict(self) -> dict[str, Any]:
        """Serialización para la capa REST y para raw_output en predictions."""
        return {
            "decision": self.decision,
            "rejection_reason": self.rejection_reason,
            "entry": self.entry,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "position_size": self.position_size,
            "rr_ratio": self.rr_ratio,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "regime_check_passed": self.regime_check_passed,
            "rules_check_passed": self.rules_check_passed,
            "rr_check_passed": self.rr_check_passed,
            "rules_detail": [
                {
                    "indicator": r.indicator,
                    "operator": r.operator,
                    "threshold": r.threshold,
                    "actual_value": r.actual_value,
                    "passed": r.passed,
                }
                for r in self.rules_detail
            ],
            "meta": self.meta,
        }
