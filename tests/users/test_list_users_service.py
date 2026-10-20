# -*- coding: utf-8 -*-

# ======================================================================
# tests/users/test_list_users_service.py
# ======================================================================

from unittest.mock import MagicMock

from tests.conftest import make_user
from app.modules.users.services.users import ListUsersService


def _make_service(users, roles):
    repo = MagicMock()
    repo.list_all.return_value = users
    repo.get_role_info.side_effect = lambda role_id: roles.get(role_id)
    return ListUsersService(repo=repo), repo


class TestListUsersService:

    def test_lists_users_with_their_role(self):
        users = [
            make_user(id=1, email="admin@x.co", role_id=2),
            make_user(id=2, email="ana@x.co", role_id=1, full_name=None),
        ]
        roles = {1: {"code": "user", "name": "Usuario"}, 2: {"code": "admin", "name": "Administrador"}}
        svc, _ = _make_service(users, roles)

        result = svc.list()

        assert result.success is True
        assert [(u.id, u.role_code) for u in result.data] == [(1, "admin"), (2, "user")]
        assert result.data[1].full_name is None

    def test_reads_each_role_only_once(self):
        users = [make_user(id=i, role_id=1) for i in range(1, 5)]
        svc, repo = _make_service(users, {1: {"code": "user", "name": "Usuario"}})

        svc.list()

        repo.get_role_info.assert_called_once_with(1)

    def test_missing_role_does_not_break_the_list(self):
        svc, _ = _make_service([make_user(id=1, role_id=9)], roles={})

        result = svc.list()

        assert result.success is True
        assert result.data[0].role_code == ""

    def test_payload_has_no_secrets(self):
        user = make_user(id=1, token_current_jti="jti-secreto", otp_code="hash")
        svc, _ = _make_service([user], {1: {"code": "user", "name": "Usuario"}})

        payload = vars(svc.list().data[0])

        assert "token_current_jti" not in payload
        assert "otp_code" not in payload
