# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/feature_sets.py
#
# PROPÓSITO:
# - 3 conjuntos de indicadores del Módulo 3, uno por enfoque, para que
#   un agente se pueda crear sin que un admin configure nada antes.
#
# NOTAS:
# - Clave natural: (name, version), igual que uq_feature_sets_name_version.
# - El `spec` sigue el formato de `indicator_catalog`: el cálculo y la IA
#   solo usan los grupos listados en `indicators`.
# - Compatibilidad con las 6 estrategias de `strategies.py`:
#   Completo → todas; Tendencia → las de tendencia y las de MACD/RSI;
#   Rango → las de reversión a la media y las de MACD/RSI.
# ======================================================================

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.modules.features.infrastructure.feature_set_model import FeatureSetModel
from database.seeds._helpers import SeedStats, get_or_create

FEATURE_SETS: list[dict[str, Any]] = [
    {
        "name": "Completo",
        "version": "1.0.0",
        "description": (
            "Todos los indicadores: RSI, medias móviles (EMA 20/50/200), MACD, ATR, "
            "bandas de Bollinger y volumen relativo. Sirve para cualquier estrategia."
        ),
        "spec": {
            "focus": "all",
            "indicators": ["rsi", "ema", "macd", "atr", "bbands", "vol_rel"],
        },
    },
    {
        "name": "Tendencia",
        "version": "1.0.0",
        "description": (
            "Para seguir tendencias: medias móviles (EMA 20/50/200) para ver la dirección, "
            "MACD y RSI para medir la fuerza, ATR para la volatilidad y volumen relativo."
        ),
        "spec": {
            "focus": "trend_following",
            "indicators": ["ema", "macd", "rsi", "atr", "vol_rel"],
        },
    },
    {
        "name": "Rango",
        "version": "1.0.0",
        "description": (
            "Para mercados laterales: RSI y bandas de Bollinger para detectar extremos, "
            "MACD para confirmar el giro, ATR para la volatilidad y volumen relativo."
        ),
        "spec": {
            "focus": "mean_reversion",
            "indicators": ["rsi", "bbands", "macd", "atr", "vol_rel"],
        },
    },
]


def run(session: Session) -> SeedStats:
    stats = SeedStats()

    for feature_set in FEATURE_SETS:
        get_or_create(
            session,
            FeatureSetModel,
            lookup={"name": feature_set["name"], "version": feature_set["version"]},
            values={
                "description": feature_set["description"],
                "spec": feature_set["spec"],
            },
            stats=stats,
        )

    return stats
