# -*- coding: utf-8 -*-

# ======================================================================
# tests/features/test_list_feature_sets_service.py
# ======================================================================

from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.modules.features.domain.feature_set_entity import FeatureSet
from app.modules.features.services.feature_sets.list_feature_sets_service import (
    ListFeatureSetsService,
)


def _make_feature_set(id: int = 1, name: str = "default", version: str = "1.0.0") -> FeatureSet:
    return FeatureSet(
        id=id,
        name=name,
        version=version,
        spec={"rsi": 14},
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _make_service(feature_sets: list) -> ListFeatureSetsService:
    repo = MagicMock()
    repo.list_all.return_value = feature_sets
    return ListFeatureSetsService(repo=repo)


class TestListFeatureSetsService:

    def test_returns_empty_list_when_no_feature_sets(self):
        svc = _make_service([])

        result = svc.list()

        assert result.success is True
        assert result.data == []

    def test_returns_all_feature_sets(self):
        feature_sets = [
            _make_feature_set(id=1, name="set_a"),
            _make_feature_set(id=2, name="set_b"),
        ]
        svc = _make_service(feature_sets)

        result = svc.list()

        assert result.success is True
        assert len(result.data) == 2
        assert result.data[0].name == "set_a"
        assert result.data[1].name == "set_b"

    def test_returns_single_feature_set(self):
        svc = _make_service([_make_feature_set(id=5, name="ema_rsi")])

        result = svc.list()

        assert result.success is True
        assert result.data[0].id == 5
        assert result.data[0].name == "ema_rsi"
