# -*- coding: utf-8 -*-

# ======================================================================
# tests/strategies/test_strategy_services.py
#
# Estrategias (M5): entidad (tipo, coherencia tipo ↔ régimen, accesos a
# `parameters`) y casos de uso crear / editar / ver / listar, con sus
# códigos de error, http_status y commit solo en éxito.
# Sin BD: repositorio MagicMock.
# ======================================================================

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.modules.strategies.domain.strategy_entity import Strategy
from app.modules.strategies.rest.strategies.error_messages import STRATEGY_ERROR_MESSAGES
from app.modules.strategies.services.strategies import (
    CreateStrategyService,
    GetStrategyService,
    ListStrategiesService,
    UpdateStrategyService,
)

RULES = [{"indicator": "ema_20", "operator": "gt", "value": "ema_50"}]


def _params(strategy_type="trend_following", regime="trend_up", **extra) -> dict:
    return {
        "strategy_type": strategy_type,
        "regime_required": regime,
        "timeframe_code": "4h",
        "rules": RULES,
        "risk_pct": 0.01,
        **extra,
    }


def _strategy(id_=1, name="EMA Trend Follower", version="1.0.0", params=None) -> Strategy:
    return Strategy(id=id_, name=name, version=version, parameters=params or _params())


def _repo(by_id: Strategy | None = None, existing: dict[tuple[str, str], Strategy] | None = None) -> MagicMock:
    """Repo cuyo get_by_name_version responde según el par (name, version) EXACTO."""
    existing = existing or {}
    repo = MagicMock()
    repo.get_by_id.return_value = by_id
    repo.get_by_name_version.side_effect = lambda name, version: existing.get((name, version))
    repo.create.side_effect = lambda s: s
    repo.update.side_effect = lambda s: s
    return repo


def _assert_failed(result, code, http_status, repo):
    assert result.success is False
    assert result.error.code == code
    assert result.error.http_status == http_status
    assert code in STRATEGY_ERROR_MESSAGES
    repo.commit.assert_not_called()


# ======================================================================
# Entidad
# ======================================================================

class TestStrategyEntity:

    @pytest.mark.parametrize("strategy_type, regime, coherent", [
        ("trend_following", "trend_up", True),
        ("trend_following", "trend_down", True),
        ("trend_following", "sideways", False),
        ("mean_reversion", "sideways", True),
        ("mean_reversion", "trend_up", False),
        ("mean_reversion", "trend_down", False),
        ("trend_following", None, True),      # sin régimen exigido → siempre coherente
        ("mean_reversion", None, True),
        ("trend_following", "bullish", False),  # régimen desconocido
        ("breakout", "trend_up", False),        # tipo desconocido con régimen
    ])
    def test_type_regime_coherence(self, strategy_type, regime, coherent):
        assert _strategy(params=_params(strategy_type, regime)).is_coherent() is coherent

    @pytest.mark.parametrize("strategy_type, valid", [
        ("trend_following", True), ("mean_reversion", True), ("breakout", False), (None, False),
    ])
    def test_valid_types(self, strategy_type, valid):
        assert _strategy(params=_params(strategy_type)).is_valid_type() is valid

    def test_accessors_read_parameters(self):
        s = _strategy()

        assert (s.strategy_type, s.regime_required, s.timeframe_code) == ("trend_following", "trend_up", "4h")
        assert s.rules == RULES

    def test_rules_default_to_empty_list(self):
        assert Strategy(id=1, name="X", version="1", parameters={}).rules == []


# ======================================================================
# CreateStrategyService
# ======================================================================

class TestCreateStrategyService:

    def test_creates_coherent_strategy_and_commits(self):
        repo = _repo()

        result = CreateStrategyService(repo).create(
            name="RSI Mean Reversion", version="1.1.0",
            parameters=_params("mean_reversion", "sideways"), description="Rango",
        )

        assert result.success is True
        assert result.data.strategy_type == "mean_reversion"
        repo.create.assert_called_once()
        repo.commit.assert_called_once()

    def test_trims_name_version_and_description(self):
        repo = _repo()

        result = CreateStrategyService(repo).create(
            name="  Tendencia Metales ", version=" 1.0.0 ", parameters=_params(), description="  oro  ",
        )

        assert (result.data.name, result.data.version, result.data.description) == (
            "Tendencia Metales", "1.0.0", "oro",
        )

    def test_empty_description_is_stored_as_none(self):
        result = CreateStrategyService(_repo()).create(name="X", version="1", parameters=_params(), description="")

        assert result.data.description is None

    def test_duplicate_name_version_is_409(self):
        repo = _repo(existing={("EMA Trend Follower", "1.0.0"): _strategy()})

        result = CreateStrategyService(repo).create(name="EMA Trend Follower", version="1.0.0", parameters=_params())

        _assert_failed(result, "STRATEGY_DUPLICATE_NAME_VERSION", 409, repo)
        repo.create.assert_not_called()

    def test_duplicate_is_detected_even_with_surrounding_spaces(self):
        # Se guarda el nombre recortado: la comprobación de duplicado debe usar
        # el mismo valor, o el UNIQUE (name, version) de la BD salta con un 500.
        repo = _repo(existing={("EMA Trend Follower", "1.0.0"): _strategy()})

        result = CreateStrategyService(repo).create(name=" EMA Trend Follower ", version="1.0.0 ", parameters=_params())

        _assert_failed(result, "STRATEGY_DUPLICATE_NAME_VERSION", 409, repo)
        repo.create.assert_not_called()

    @pytest.mark.parametrize("params", [
        _params("breakout"),
        {"regime_required": "trend_up", "rules": RULES},   # sin strategy_type
    ])
    def test_invalid_type_is_422(self, params):
        repo = _repo()

        _assert_failed(CreateStrategyService(repo).create(name="X", version="1", parameters=params), "STRATEGY_INVALID_TYPE", 422, repo)
        repo.create.assert_not_called()

    @pytest.mark.parametrize("strategy_type, regime", [
        ("trend_following", "sideways"),
        ("mean_reversion", "trend_up"),
        ("mean_reversion", "trend_down"),
    ])
    def test_incoherent_regime_is_422(self, strategy_type, regime):
        repo = _repo()

        result = CreateStrategyService(repo).create(name="X", version="1", parameters=_params(strategy_type, regime))

        _assert_failed(result, "STRATEGY_INCOHERENT_REGIME", 422, repo)
        repo.create.assert_not_called()


# ======================================================================
# UpdateStrategyService
# ======================================================================

class TestUpdateStrategyService:

    def test_not_found_is_404(self):
        repo = _repo(by_id=None)

        _assert_failed(UpdateStrategyService(repo).update(9, name="X"), "STRATEGY_NOT_FOUND", 404, repo)

    def test_rename_onto_another_strategy_is_409(self):
        other = _strategy(id_=2, name="MACD Crossover")
        repo = _repo(by_id=_strategy(id_=1), existing={("MACD Crossover", "1.0.0"): other})

        _assert_failed(UpdateStrategyService(repo).update(1, name="MACD Crossover"), "STRATEGY_DUPLICATE_NAME_VERSION", 409, repo)
        repo.update.assert_not_called()

    def test_same_name_version_of_itself_is_not_a_collision(self):
        current = _strategy(id_=1)
        repo = _repo(by_id=current, existing={("EMA Trend Follower", "1.0.0"): current})

        result = UpdateStrategyService(repo).update(1, description="  nueva  ")

        assert result.success is True
        assert result.data.description == "nueva"
        assert result.data.parameters == _params()        # sin parameters → no cambian
        repo.commit.assert_called_once()

    def test_new_parameters_are_revalidated_for_coherence(self):
        repo = _repo(by_id=_strategy())

        result = UpdateStrategyService(repo).update(1, parameters=_params("trend_following", "sideways"))

        _assert_failed(result, "STRATEGY_INCOHERENT_REGIME", 422, repo)
        repo.update.assert_not_called()

    def test_new_parameters_with_invalid_type_is_422(self):
        repo = _repo(by_id=_strategy())

        _assert_failed(UpdateStrategyService(repo).update(1, parameters={"rules": []}), "STRATEGY_INVALID_TYPE", 422, repo)

    def test_new_version_and_parameters_are_saved_trimmed(self):
        repo = _repo(by_id=_strategy())
        new_params = _params("mean_reversion", "sideways")

        result = UpdateStrategyService(repo).update(1, version=" 2.0.0 ", parameters=new_params)

        assert (result.data.version, result.data.parameters) == ("2.0.0", new_params)
        repo.get_by_name_version.assert_called_with("EMA Trend Follower", "2.0.0")
        repo.commit.assert_called_once()


# ======================================================================
# Get / List
# ======================================================================

class TestGetAndListStrategies:

    def test_get_not_found_is_404(self):
        result = GetStrategyService(_repo(by_id=None)).get(5)

        assert (result.error.code, result.error.http_status) == ("STRATEGY_NOT_FOUND", 404)

    def test_get_returns_strategy(self):
        assert GetStrategyService(_repo(by_id=_strategy(id_=5))).get(5).data.id == 5

    def test_list_returns_repo_list(self):
        repo = _repo()
        repo.list_all.return_value = [_strategy(1), _strategy(2)]

        assert [s.id for s in ListStrategiesService(repo).list().data] == [1, 2]


# ======================================================================
# Mensajes de UI del backtesting
# ======================================================================

@pytest.mark.parametrize("code", [
    # RunBacktestService
    "STRATEGY_NOT_FOUND", "BACKTEST_STRATEGY_WITHOUT_RULES", "BACKTEST_NOT_ENOUGH_HISTORY",
    # FetchCandleHistoryService (M2), que el backtest devuelve tal cual
    "SYMBOL_NOT_FOUND", "TIMEFRAME_NOT_FOUND", "EXCHANGE_NOT_SUPPORTED_CCXT",
    "CCXT_SYMBOL_NOT_FOUND", "CCXT_NETWORK_ERROR", "CCXT_FETCH_ERROR",
])
def test_every_backtest_error_code_has_a_ui_message(code):
    from app.modules.strategies.rest.backtests.error_messages import BACKTEST_ERROR_MESSAGES

    assert BACKTEST_ERROR_MESSAGES.get(code, "").strip()
