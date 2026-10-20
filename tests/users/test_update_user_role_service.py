# -*- coding: utf-8 -*-

# ======================================================================
# tests/users/test_update_user_role_service.py
# ======================================================================

from unittest.mock import MagicMock

from tests.conftest import make_user
from app.modules.users.services.users import UpdateUserRoleService

ROLE_IDS = {"user": 1, "admin": 2, "investor": 3}
ROLES = {
    1: {"code": "user", "name": "Usuario"},
    2: {"code": "admin", "name": "Administrador"},
    3: {"code": "investor", "name": "Inversor"},
}


def _make_service(user=None, roles=ROLES):
    repo = MagicMock()
    repo.get_by_id.return_value = user
    repo.get_role_info.side_effect = lambda role_id: roles.get(role_id)
    repo.update.side_effect = lambda u: u
    return UpdateUserRoleService(repo=repo, role_ids=ROLE_IDS), repo


class TestUpdateUserRoleService:

    def test_changes_role_and_commits(self):
        user = make_user(id=7, role_id=1)
        svc, repo = _make_service(user)

        result = svc.update(user_id=7, role_code="investor", requester_user_id=1)

        assert result.success is True
        assert result.data.role_code == "investor"
        assert result.data.role_name == "Inversor"
        assert user.role_id == 3
        repo.commit.assert_called_once()

    def test_same_role_does_not_write(self):
        user = make_user(id=7, role_id=2)
        svc, repo = _make_service(user)

        result = svc.update(user_id=7, role_code="admin", requester_user_id=1)

        assert result.success is True
        assert result.data.role_code == "admin"
        repo.update.assert_not_called()
        repo.commit.assert_not_called()

    def test_cannot_change_own_role(self):
        svc, repo = _make_service(make_user(id=1, role_id=2))

        result = svc.update(user_id=1, role_code="user", requester_user_id=1)

        assert result.success is False
        assert result.error.code == "USER_CANNOT_CHANGE_OWN_ROLE"
        assert result.error.http_status == 422
        repo.commit.assert_not_called()

    def test_unknown_role_code_fails(self):
        svc, repo = _make_service(make_user(id=7))

        result = svc.update(user_id=7, role_code="root", requester_user_id=1)

        assert result.error.code == "USER_INVALID_ROLE"
        assert result.error.http_status == 422
        repo.get_by_id.assert_not_called()

    def test_role_missing_in_db_fails(self):
        # El ID del setting no existe en la tabla roles
        svc, repo = _make_service(make_user(id=7), roles={})

        result = svc.update(user_id=7, role_code="admin", requester_user_id=1)

        assert result.error.code == "USER_INVALID_ROLE"
        repo.commit.assert_not_called()

    def test_user_not_found(self):
        svc, repo = _make_service(user=None)

        result = svc.update(user_id=99, role_code="admin", requester_user_id=1)

        assert result.error.code == "USER_NOT_FOUND"
        assert result.error.http_status == 404
        repo.commit.assert_not_called()
