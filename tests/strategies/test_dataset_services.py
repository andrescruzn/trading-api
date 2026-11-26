# -*- coding: utf-8 -*-

# ======================================================================
# tests/strategies/test_dataset_services.py
#
# Datasets de backtesting (M5): crear (rango de fechas válido, textos
# recortados), ver y listar. Sin BD: repositorio MagicMock.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.modules.strategies.domain.dataset_entity import Dataset
from app.modules.strategies.rest.datasets.error_messages import DATASET_ERROR_MESSAGES
from app.modules.strategies.services.datasets import (
    CreateDatasetService,
    GetDatasetService,
    ListDatasetsService,
)

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _repo() -> MagicMock:
    repo = MagicMock()
    repo.create.side_effect = lambda d: d
    return repo


class TestCreateDatasetService:

    def test_creates_dataset_and_commits(self):
        repo = _repo()
        spec = {"feature_set_id": 3}

        result = CreateDatasetService(repo).create(
            name="  BTC 1h 2026 ", query_spec=spec, description="  enero  ",
            symbol_id=1, timeframe_id=6, start_ts=START, end_ts=START + timedelta(days=31),
        )

        assert result.success is True
        assert (result.data.name, result.data.description) == ("BTC 1h 2026", "enero")
        assert (result.data.symbol_id, result.data.timeframe_id, result.data.query_spec) == (1, 6, spec)
        repo.commit.assert_called_once()

    def test_end_equal_to_start_is_invalid_range(self):
        repo = _repo()

        result = CreateDatasetService(repo).create(name="X", query_spec={}, start_ts=START, end_ts=START)

        assert (result.error.code, result.error.http_status) == ("DATASET_INVALID_DATE_RANGE", 422)
        assert result.error.code in DATASET_ERROR_MESSAGES
        repo.create.assert_not_called()
        repo.commit.assert_not_called()

    def test_end_before_start_is_invalid_range(self):
        repo = _repo()

        result = CreateDatasetService(repo).create(
            name="X", query_spec={}, start_ts=START, end_ts=START - timedelta(hours=1),
        )

        assert result.error.code == "DATASET_INVALID_DATE_RANGE"
        repo.commit.assert_not_called()

    def test_open_ranges_are_allowed(self):
        for start, end in ((START, None), (None, START), (None, None)):
            repo = _repo()
            result = CreateDatasetService(repo).create(name="X", query_spec={}, start_ts=start, end_ts=end)
            assert result.success is True
            repo.commit.assert_called_once()

    def test_without_description_stores_none(self):
        result = CreateDatasetService(_repo()).create(name="X", query_spec={})

        assert result.data.description is None


class TestGetAndListDatasets:

    def test_get_not_found_is_404(self):
        repo = _repo()
        repo.get_by_id.return_value = None

        result = GetDatasetService(repo).get(7)

        assert (result.error.code, result.error.http_status) == ("DATASET_NOT_FOUND", 404)
        assert result.error.code in DATASET_ERROR_MESSAGES

    def test_get_and_list_return_repo_data(self):
        repo = _repo()
        dataset = Dataset(id=7, name="X", query_spec={})
        repo.get_by_id.return_value = dataset
        repo.list_all.return_value = [dataset]

        assert GetDatasetService(repo).get(7).data is dataset
        assert ListDatasetsService(repo).list().data == [dataset]
