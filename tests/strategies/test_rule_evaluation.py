# -*- coding: utf-8 -*-

# ======================================================================
# tests/strategies/test_rule_evaluation.py
#
# Evaluación de reglas (domain/rule_evaluation.py), la MISMA función que
# usan la IA (M6, fase de reglas) y el backtesting (M5). Fail-closed:
# una regla inválida o sin dato nunca se cumple.
# ======================================================================

from __future__ import annotations

import math

import pytest

from app.modules.strategies.domain.rule_evaluation import OPERATORS, evaluate_rule, rules_pass

FEATURES = {"rsi_14": 28.5, "ema_20": 105.2, "ema_50": 101.7, "bb_bandwidth": 3.0, "regime": "sideways"}


def _rule(indicator, operator, value):
    return {"indicator": indicator, "operator": operator, "value": value}


class TestEvaluateRule:

    @pytest.mark.parametrize("operator, value, expected", [
        ("lt", 30, True),
        ("lt", 28.5, False),
        ("lte", 28.5, True),
        ("gt", 28, True),
        ("gt", 28.5, False),
        ("gte", 28.5, True),
        ("gte", 29, False),
        ("eq", 28.5, True),
    ])
    def test_numeric_operators(self, operator, value, expected):
        passed, actual = evaluate_rule(_rule("rsi_14", operator, value), FEATURES)

        assert passed is expected
        assert actual == 28.5

    def test_eq_tolerates_float_noise_below_0_0001(self):
        assert evaluate_rule(_rule("bb_bandwidth", "eq", 3.00005), FEATURES)[0] is True
        assert evaluate_rule(_rule("bb_bandwidth", "eq", 3.001), FEATURES)[0] is False

    def test_value_can_be_another_indicator(self):
        # ema_20 (105,2) > ema_50 (101,7)
        assert evaluate_rule(_rule("ema_20", "gt", "ema_50"), FEATURES) == (True, 105.2)
        assert evaluate_rule(_rule("ema_50", "gt", "ema_20"), FEATURES) == (False, 101.7)

    def test_numeric_string_threshold_is_accepted(self):
        assert evaluate_rule(_rule("rsi_14", "lt", "30"), FEATURES)[0] is True

    @pytest.mark.parametrize("rule, features", [
        (_rule("rsi_14", "lt", "ema_200"), FEATURES),            # el otro indicador no existe
        (_rule("vol_rel", "gt", 1.5), FEATURES),                 # indicador sin dato
        (_rule("rsi_14", "below", 30), FEATURES),                # operador desconocido
        (_rule("rsi_14", "lt", None), FEATURES),                 # sin umbral
        (_rule("rsi_14", "lt", [30]), FEATURES),                 # umbral de tipo raro
        (_rule("regime", "gt", 1), FEATURES),                    # indicador no numérico
        (_rule("rsi_14", "lt", 30), {"rsi_14": None}),           # dato nulo
        (_rule("ema_20", "gt", "ema_50"), {"ema_20": 1.0, "ema_50": None}),
        ({}, FEATURES),                                          # regla vacía
    ])
    def test_invalid_rule_or_missing_data_fails_closed(self, rule, features):
        assert evaluate_rule(rule, features)[0] is False

    @pytest.mark.parametrize("operator", sorted(OPERATORS))
    def test_nan_indicator_never_passes(self, operator):
        assert evaluate_rule(_rule("rsi_14", operator, 30), {"rsi_14": math.nan})[0] is False

    def test_returns_actual_value_even_when_it_fails(self):
        assert evaluate_rule(_rule("rsi_14", "below", 30), FEATURES) == (False, 28.5)
        assert evaluate_rule(_rule("vol_rel", "gt", 1), FEATURES) == (False, None)


class TestRulesPass:

    def test_no_rules_pass(self):
        assert rules_pass([], FEATURES) is True

    def test_all_rules_must_pass(self):
        rules = [_rule("rsi_14", "lt", 30), _rule("ema_20", "gt", "ema_50"), _rule("bb_bandwidth", "lt", 5)]

        assert rules_pass(rules, FEATURES) is True
        assert rules_pass([*rules, _rule("bb_bandwidth", "gt", 1)], FEATURES) is True

    def test_one_failing_rule_blocks_the_entry(self):
        # RSI Mean Reversion 1.1.0: rsi_14 < 30 y bb_bandwidth < 3 → 3,0 no es < 3
        rules = [_rule("rsi_14", "lt", 30), _rule("bb_bandwidth", "lt", 3)]

        assert rules_pass(rules, FEATURES) is False

    def test_one_broken_rule_blocks_the_entry(self):
        assert rules_pass([_rule("rsi_14", "lt", 30), _rule("typo_14", "gt", 0)], FEATURES) is False
