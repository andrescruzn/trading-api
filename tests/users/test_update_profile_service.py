# -*- coding: utf-8 -*-

# ======================================================================
# tests/users/test_update_profile_service.py
# ======================================================================

from unittest.mock import MagicMock

from tests.conftest import make_user
from app.modules.users.services.users import UpdateProfileService


def _make(user):
    repo = MagicMock()
    repo.get_by_id.return_value = user
    repo.update.side_effect = lambda u: u
    return UpdateProfileService(repo=repo), repo


class TestUpdateProfileService:

    def test_changes_name_trimmed(self):
        user = make_user(full_name="Viejo")
        svc, repo = _make(user)

        result = svc.update(user_id=1, full_name="  Ana Pérez ")

        assert result.data.full_name == "Ana Pérez"
        repo.commit.assert_called_once()

    def test_blank_name_clears_it(self):
        user = make_user(full_name="Ana")
        svc, _ = _make(user)

        assert svc.update(user_id=1, full_name="   ").data.full_name is None

    def test_same_name_does_not_write(self):
        svc, repo = _make(make_user(full_name="Ana"))

        svc.update(user_id=1, full_name="Ana")

        repo.update.assert_not_called()
        repo.commit.assert_not_called()

    def test_user_not_found(self):
        svc, _ = _make(None)

        assert svc.update(user_id=9, full_name="Ana").error.code == "USER_NOT_FOUND"
