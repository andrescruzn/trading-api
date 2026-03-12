# -*- coding: utf-8 -*-

# ======================================================================
# tests/features/test_create_feature_set_service.py
# ======================================================================

from unittest.mock import MagicMock

from app.modules.features.domain.feature_set_entity import FeatureSet
from app.modules.features.services.feature_sets.create_feature_set_service import (
    CreateFeatureSetService,
)


def _make_service(existing: FeatureSet | None = None) -> tuple:
    repo = MagicMock()
    repo.get_by_name_version.return_value = existing
    session = MagicMock()
    svc = CreateFeatureSetService(repo=repo, session=session)
    return svc, repo, session


def _make_feature_set(id: int = 1, name: str = "default", version: str = "1.0.0") -> FeatureSet:
    return FeatureSet(id=id, name=name, version=version, spec={"rsi": 14})


class TestCreateFeatureSetService:

    # ------------------------------------------------------------------
    # Éxito
    # ------------------------------------------------------------------

    def test_creates_feature_set_successfully(self):
        created = _make_feature_set(id=1, name="full_set", version="1.0.0")
        svc, repo, session = _make_service(existing=None)
        repo.create.return_value = created

        result = svc.create(
            name="full_set",
            version="1.0.0",
            spec={"rsi": 14, "ema": [20, 50, 200]},
            description="Indicadores completos",
        )

        assert result.success is True
        assert result.data.name == "full_set"
        assert result.data.version == "1.0.0"
        repo.create.assert_called_once()
        session.commit.assert_called_once()

    def test_creates_feature_set_without_description(self):
        created = _make_feature_set(id=2, name="minimal")
        svc, repo, session = _make_service(existing=None)
        repo.create.return_value = created

        result = svc.create(name="minimal", version="1.0.0", spec={})

        assert result.success is True
        session.commit.assert_called_once()

    # ------------------------------------------------------------------
    # Duplicado
    # ------------------------------------------------------------------

    def test_fails_if_name_version_already_exists(self):
        existing = _make_feature_set(id=1, name="default", version="1.0.0")
        svc, repo, session = _make_service(existing=existing)

        result = svc.create(name="default", version="1.0.0", spec={"rsi": 14})

        assert result.success is False
        assert result.error.code == "FEATURE_SET_ALREADY_EXISTS"
        assert result.error.http_status == 409
        repo.create.assert_not_called()
        session.commit.assert_not_called()

    def test_allows_same_name_with_different_version(self):
        created = _make_feature_set(id=3, name="default", version="2.0.0")
        svc, repo, session = _make_service(existing=None)
        repo.create.return_value = created

        result = svc.create(name="default", version="2.0.0", spec={"rsi": 14})

        assert result.success is True
        assert result.data.version == "2.0.0"
