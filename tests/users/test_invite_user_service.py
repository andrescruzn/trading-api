# -*- coding: utf-8 -*-

# ======================================================================
# tests/users/test_invite_user_service.py
# ======================================================================

from unittest.mock import MagicMock

from tests.conftest import make_user
from app.modules.users.services.users import InviteUserService

ROLE_IDS = {"user": 1, "admin": 2, "investor": 3}
ROLES = {
    1: {"code": "user", "name": "Usuario"},
    2: {"code": "admin", "name": "Administrador"},
    3: {"code": "investor", "name": "Inversor"},
}


def _make_service(existing=None):
    repo = MagicMock()
    repo.get_by_email.return_value = existing
    repo.get_role_info.side_effect = lambda role_id: ROLES.get(role_id)
    repo.create.side_effect = lambda u: make_user(
        id=42, email=u.email, role_id=u.role_id, full_name=u.full_name
    )
    mailer = MagicMock()
    svc = InviteUserService(
        repo=repo, mailer=mailer, role_ids=ROLE_IDS, login_url="https://app.test/#/login"
    )
    return svc, repo, mailer


class TestInviteUserService:

    def test_creates_active_user_and_sends_welcome(self):
        svc, repo, mailer = _make_service()

        result = svc.invite(email="  Ana@Ejemplo.COM ", role_code="investor", full_name=" Ana ")

        assert result.success is True
        assert result.data.id == 42
        assert result.data.role_code == "investor"
        created = repo.create.call_args.args[0]
        assert (created.email, created.role_id, created.status, created.full_name) == (
            "ana@ejemplo.com", 3, "active", "Ana",
        )
        repo.commit.assert_called_once()
        kwargs = mailer.send_by_template_in_background.call_args.kwargs
        assert kwargs["to_email"] == "ana@ejemplo.com"
        assert kwargs["context"]["login_url"] == "https://app.test/#/login"

    def test_email_already_taken(self):
        svc, repo, mailer = _make_service(existing=make_user(email="ana@ejemplo.com"))

        result = svc.invite(email="ana@ejemplo.com", role_code="user")

        assert result.error.code == "USER_EMAIL_TAKEN"
        assert result.error.http_status == 409
        repo.create.assert_not_called()
        mailer.send_by_template_in_background.assert_not_called()

    def test_invalid_email(self):
        svc, repo, _ = _make_service()

        result = svc.invite(email="no-es-correo", role_code="user")

        assert result.error.code == "USER_INVALID_EMAIL"
        repo.create.assert_not_called()

    def test_invalid_role(self):
        svc, repo, _ = _make_service()

        result = svc.invite(email="ana@ejemplo.com", role_code="root")

        assert result.error.code == "USER_INVALID_ROLE"
        repo.create.assert_not_called()

    def test_name_is_optional(self):
        svc, repo, _ = _make_service()

        result = svc.invite(email="ana@ejemplo.com", role_code="user", full_name="   ")

        assert result.success is True
        assert repo.create.call_args.args[0].full_name is None
