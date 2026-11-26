# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/domain/rule_evaluation.py
#
# Evaluación determinista de una regla de estrategia contra los
# indicadores de una vela. La usan el agente de IA (M6, fase de reglas)
# y el backtesting (M5), para que ambos decidan exactamente igual.
#
# Formato de regla: {"indicator": "rsi_14", "operator": "lt", "value": 30}
# `value` puede ser un número o el nombre de otro indicador
# (ema_20 > ema_50). Fail-closed: regla inválida o sin dato → no se cumple.
# ======================================================================

from __future__ import annotations

from typing import Any, Callable

OPERATORS: dict[str, Callable[[float, float], bool]] = {
    "lt":  lambda a, b: a < b,
    "gt":  lambda a, b: a > b,
    "lte": lambda a, b: a <= b,
    "gte": lambda a, b: a >= b,
    "eq":  lambda a, b: abs(a - b) < 0.0001,
}


def evaluate_rule(rule: dict, features: dict) -> tuple[bool, Any]:
    """Devuelve (se cumple, valor real del indicador)."""
    indicator = rule.get("indicator", "")
    operator = rule.get("operator", "")
    threshold = rule.get("value")

    actual = features.get(indicator)

    # El umbral puede ser el nombre de otro indicador
    if isinstance(threshold, str) and threshold in features:
        compare = features[threshold]
    else:
        try:
            compare = float(threshold)
        except (TypeError, ValueError):
            compare = None

    if actual is None or compare is None or operator not in OPERATORS:
        return False, actual
    try:
        return OPERATORS[operator](float(actual), float(compare)), actual
    except Exception:
        return False, actual


def rules_pass(rules: list[dict], features: dict) -> bool:
    """Todas las reglas se cumplen (sin reglas, se cumple)."""
    return all(evaluate_rule(rule, features)[0] for rule in rules)
