# -*- coding: utf-8 -*-

# ======================================================================
# tests/users/test_update_user_role_service.py
# ======================================================================

from unittest.mock import MagicMock

from tests.conftest import make_user
from app.modules.users.services.users import UpdateUserRoleService

# Roles asignables desde la app (super admin no se asigna)
ROLE_IDS = {"partner": 4, "investor": 3}
SUPER_ADMIN_ROLE_ID = 2
ROLES = {
    2: {"code": "super_admin", "name": "Super admin"},
    3: {"code": "investor", "name": "Inversor"},
    4: {"code": "partner", "name": "Socio"},
}


def _make_service(user=None, roles=ROLES):
    repo = MagicMock()
    repo.get_by_id.return_value = user
    repo.get_role_info.side_effect = lambda role_id: roles.get(role_id)
    repo.update.side_effect = lambda u: u
    return (
        UpdateUserRoleService(
            repo=repo, role_ids=ROLE_IDS, protected_role_id=SUPER_ADMIN_ROLE_ID
        ),
        repo,
    )


class TestUpdateUserRoleService:

    def test_changes_role_and_commits(self):
        user = make_user(id=7, role_id=3)
        svc, repo = _make_service(user)

        result = svc.update(user_id=7, role_code="partner", requester_user_id=1)

        assert result.success is True
        assert result.data.role_code == "partner"
        assert result.data.role_name == "Socio"
        assert user.role_id == 4
        repo.commit.assert_called_once()

    def test_same_role_does_not_write(self):
        user = make_user(id=7, role_id=4)
        svc, repo = _make_service(user)

        result = svc.update(user_id=7, role_code="partner", requester_user_id=1)

        assert result.success is True
        assert result.data.role_code == "partner"
        repo.update.assert_not_called()
        repo.commit.assert_not_called()

    def test_cannot_change_own_role(self):
        svc, repo = _make_service(make_user(id=1, role_id=3))

        result = svc.update(user_id=1, role_code="partner", requester_user_id=1)

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
        svc, repo = _make_service(make_user(id=7, role_id=3), roles={})

        result = svc.update(user_id=7, role_code="partner", requester_user_id=1)

        assert result.error.code == "USER_INVALID_ROLE"
        repo.commit.assert_not_called()

    def test_user_not_found(self):
        svc, repo = _make_service(user=None)

        result = svc.update(user_id=99, role_code="partner", requester_user_id=1)

        assert result.error.code == "USER_NOT_FOUND"
        assert result.error.http_status == 404
        repo.commit.assert_not_called()
