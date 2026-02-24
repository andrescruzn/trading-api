# -*- coding: utf-8 -*-

# ======================================================================
# tests/users/test_login_password_service.py
# ======================================================================

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from tests.conftest import make_user, make_mock_repo
from app.modules.users.services.auth.login_password_service import LoginPasswordService


def _make_settings():
    s = MagicMock()
    s.JWT_SECRET_KEY = "test-secret"
    s.JWT_ALGORITHM = "HS256"
    s.JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    return s


def _make_service(user=None, settings=None):
    repo = make_mock_repo(user)
    session = MagicMock()
    svc = LoginPasswordService(
        repo=repo,
        session=session,
        settings=settings or _make_settings(),
    )
    return svc, repo, session


class TestLoginPasswordService:

    # ------------------------------------------------------------------
    # Éxito
    # ------------------------------------------------------------------

    @patch("app.modules.users.services.auth.login_password_service.verify_password")
    @patch("app.modules.users.services.auth.login_password_service.create_access_token")
    def test_login_success(self, mock_token, mock_verify):
        mock_verify.return_value = True
        mock_token.return_value = {
            "token": "jwt.token.here",
            "jti": "test-jti",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        user = make_user(token_current_jti=None)
        svc, repo, session = _make_service(user)

        result = svc.login("test@example.com", "Password1")

        assert result.success is True
        assert result.data.access_token == "jwt.token.here"
        assert result.data.jti == "test-jti"
        assert user.token_current_jti == "test-jti"
        assert user.otp_code is None
        session.commit.assert_called_once()

    # ------------------------------------------------------------------
    # Usuario no encontrado (anti-enumeration)
    # ------------------------------------------------------------------

    def test_user_not_found_returns_invalid_credentials(self):
        svc, _, _ = _make_service(user=None)

        result = svc.login("noexiste@test.com", "Password1")

        assert result.success is False
        assert result.error.code == "INVALID_CREDENTIALS"
        assert result.error.http_status == 401

    # ------------------------------------------------------------------
    # Password incorrecta
    # ------------------------------------------------------------------

    @patch("app.modules.users.services.auth.login_password_service.verify_password")
    def test_wrong_password_increments_attempts(self, mock_verify):
        mock_verify.return_value = False
        user = make_user(failed_attempts=0)
        svc, repo, session = _make_service(user)

        result = svc.login("test@example.com", "WrongPass")

        assert result.success is False
        assert result.error.code == "INVALID_CREDENTIALS"
        repo.update.assert_called_once()
        session.commit.assert_called_once()

    # ------------------------------------------------------------------
    # Cuenta bloqueada
    # ------------------------------------------------------------------

    def test_locked_account(self):
        locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
        user = make_user(login_locked_until=locked_until)
        svc, _, _ = _make_service(user)

        result = svc.login("test@example.com", "Password1")

        assert result.success is False
        assert result.error.code == "LOGIN_LOCKED"
        assert result.error.http_status == 429

    # ------------------------------------------------------------------
    # Usuario inactivo
    # ------------------------------------------------------------------

    def test_inactive_user(self):
        user = make_user(status="blocked")
        svc, _, _ = _make_service(user)

        result = svc.login("test@example.com", "Password1")

        assert result.success is False
        assert result.error.code == "USER_NOT_ALLOWED"
        assert result.error.http_status == 403

    # ------------------------------------------------------------------
    # Input inválido
    # ------------------------------------------------------------------

    def test_invalid_email_format(self):
        svc, _, _ = _make_service()

        result = svc.login("not-an-email", "Password1")

        assert result.success is False
        assert result.error.code == "VALIDATION_ERROR"

    def test_empty_password(self):
        svc, _, _ = _make_service()

        result = svc.login("test@example.com", "")

        assert result.success is False
        assert result.error.code == "VALIDATION_ERROR"

    # ------------------------------------------------------------------
    # Verifica que usa utc_now() (consistencia)
    # ------------------------------------------------------------------

    @patch("app.modules.users.services.auth.login_password_service.verify_password")
    @patch("app.modules.users.services.auth.login_password_service.utc_now")
    @patch("app.modules.users.services.auth.login_password_service.create_access_token")
    def test_uses_utc_now(self, mock_token, mock_utc, mock_verify):
        fixed_now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        mock_utc.return_value = fixed_now
        mock_verify.return_value = True
        mock_token.return_value = {
            "token": "t", "jti": "j",
            "expires_at": fixed_now + timedelta(hours=1),
        }
        user = make_user()
        svc, _, _ = _make_service(user)

        svc.login("test@example.com", "Password1")

        mock_utc.assert_called_once()
