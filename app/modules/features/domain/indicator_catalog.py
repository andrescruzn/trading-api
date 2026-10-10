# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/domain/indicator_catalog.py
#
# PROPÓSITO:
# - Catálogo de los indicadores que sabe calcular el sistema, agrupados
#   por familia, y reglas para leer el `spec` de un FeatureSet.
#
# FORMATO DEL SPEC:
#   {"focus": "all" | "trend_following" | "mean_reversion",
#    "indicators": ["rsi", "ema", "macd", "atr", "bbands", "vol_rel"]}
#
# NOTAS:
# - Un spec sin `indicators` (sets creados antes de este catálogo)
#   equivale a todos los grupos: así siguen funcionando igual.
# - `regime` se calcula siempre: el filtro de régimen es regla de negocio.
# - Dominio puro: sin FastAPI ni SQLAlchemy.
# ======================================================================

from __future__ import annotations

from typing import Any

# Grupo de indicadores → claves que produce en `candle_features.features`
INDICATOR_GROUPS: dict[str, tuple[str, ...]] = {
    "rsi": ("rsi_14",),
    "ema": ("ema_20", "ema_50", "ema_200"),
    "macd": ("macd", "macd_signal", "macd_hist"),
    "atr": ("atr_14",),
    "bbands": ("bb_upper", "bb_mid", "bb_lower", "bb_bandwidth"),
    "vol_rel": ("vol_rel",),
}

VALID_FOCUS = frozenset({"all", "trend_following", "mean_reversion"})

# Claves que existen siempre, sea cual sea el conjunto
ALWAYS_PRESENT: frozenset[str] = frozenset({"regime"})


def groups_for(spec: dict[str, Any] | None) -> tuple[str, ...]:
    """Grupos activos del spec, en el orden del catálogo. Sin `indicators` → todos."""
    requested = (spec or {}).get("indicators")
    if not isinstance(requested, list) or not requested:
        return tuple(INDICATOR_GROUPS)
    return tuple(g for g in INDICATOR_GROUPS if g in requested)


def outputs_for(spec: dict[str, Any] | None) -> set[str]:
    """Claves de features que produce un spec (incluye `regime`)."""
    keys: set[str] = set(ALWAYS_PRESENT)
    for group in groups_for(spec):
        keys.update(INDICATOR_GROUPS[group])
    return keys


def focus_of(spec: dict[str, Any] | None) -> str:
    """Enfoque declarado del conjunto; `all` si no lo declara o no es válido."""
    focus = (spec or {}).get("focus")
    return focus if focus in VALID_FOCUS else "all"


def invalid_groups(spec: dict[str, Any] | None) -> list[str]:
    """Grupos del spec que el catálogo no conoce (para validar al crear)."""
    requested = (spec or {}).get("indicators")
    if not isinstance(requested, list):
        return []
    return [str(g) for g in requested if g not in INDICATOR_GROUPS]


def rule_keys(rules: list[dict[str, Any]] | None) -> set[str]:
    """
    Claves de features que referencian las reglas de una estrategia.

    Una regla usa su `indicator` y, si `value` es texto no numérico, también
    lo compara contra otro indicador (p. ej. `ema_20 gt ema_50`).
    """
    keys: set[str] = set()
    for rule in rules or []:
        indicator = rule.get("indicator")
        if isinstance(indicator, str):
            keys.add(indicator)
        value = rule.get("value")
        if isinstance(value, str) and not _is_number(value):
            keys.add(value)
    return keys


def _is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def missing_for_rules(rules: list[dict[str, Any]] | None, outputs: set[str]) -> set[str]:
    """Indicadores que piden las reglas y el conjunto no calcula."""
    return rule_keys(rules) - outputs


def is_compatible(rules: list[dict[str, Any]] | None, outputs: set[str]) -> bool:
    """True si el conjunto calcula todo lo que necesitan las reglas."""
    return not missing_for_rules(rules, outputs)
