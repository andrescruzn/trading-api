# -*- coding: utf-8 -*-

# ======================================================================
# tests/users/test_change_password_service.py
# ======================================================================

from unittest.mock import MagicMock, patch

import pytest
from tests.conftest import make_user, make_mock_repo
from app.modules.users.services.auth.change_password_service import (
    ChangePasswordService,
    _validate_password_strength,
)


# ======================================================================
# Password strength validator
# ======================================================================

class TestValidatePasswordStrength:

    def test_valid_password(self):
        assert _validate_password_strength("Secure1234") is True

    def test_too_short(self):
        assert _validate_password_strength("Sec1") is False

    def test_no_uppercase(self):
        assert _validate_password_strength("secure1234") is False

    def test_no_lowercase(self):
        assert _validate_password_strength("SECURE1234") is False

    def test_no_number(self):
        assert _validate_password_strength("SecurePass") is False

    def test_exactly_8_chars_valid(self):
        assert _validate_password_strength("Secure1!") is True


# ======================================================================
# ChangePasswordService
# ======================================================================

CURRENT_HASH = "$2b$12$real_hash"


def _make_service(user=None):
    repo = make_mock_repo(user)
    session = MagicMock()
    session.commit.return_value = None
    return ChangePasswordService(repo=repo, session=session), repo, session


class TestChangePasswordService:

    # ------------------------------------------------------------------
    # Éxito
    # ------------------------------------------------------------------

    @patch("app.modules.users.services.auth.change_password_service.verify_password")
    @patch("app.modules.users.services.auth.change_password_service.hash_password")
    def test_change_password_success(self, mock_hash, mock_verify):
        mock_verify.side_effect = lambda plain, hashed: plain == "OldPass1"
        mock_hash.return_value = "$2b$12$new_hash"

        user = make_user(password_hash=CURRENT_HASH, token_current_jti="old-jti")
        svc, repo, session = _make_service(user)

        result = svc.change(
            user_id=1,
            current_password="OldPass1",
            new_password="NewSecure1",
        )

        assert result.success is True
        assert user.password_hash == "$2b$12$new_hash"
        assert user.token_current_jti is None   # sesión revocada
        repo.update.assert_called_once()
        session.commit.assert_called_once()

    # ------------------------------------------------------------------
    # Usuario no encontrado
    # ------------------------------------------------------------------

    def test_user_not_found(self):
        svc, _, _ = _make_service(user=None)

        result = svc.change(1, "OldPass1", "NewSecure1")

        assert result.success is False
        assert result.error.code == "USER_NOT_FOUND"
        assert result.error.http_status == 404

    # ------------------------------------------------------------------
    # Usuario inactivo
    # ------------------------------------------------------------------

    def test_inactive_user(self):
        user = make_user(status="blocked")
        svc, _, _ = _make_service(user)

        result = svc.change(1, "OldPass1", "NewSecure1")

        assert result.success is False
        assert result.error.code == "USER_NOT_ALLOWED"
        assert result.error.http_status == 403

    # ------------------------------------------------------------------
    # Password actual incorrecta
    # ------------------------------------------------------------------

    @patch("app.modules.users.services.auth.change_password_service.verify_password")
    def test_wrong_current_password(self, mock_verify):
        mock_verify.return_value = False
        user = make_user()
        svc, _, _ = _make_service(user)

        result = svc.change(1, "WrongPass1", "NewSecure1")

        assert result.success is False
        assert result.error.code == "INVALID_CREDENTIALS"
        assert result.error.http_status == 401

    # ------------------------------------------------------------------
    # Nueva password igual a la actual
    # ------------------------------------------------------------------

    @patch("app.modules.users.services.auth.change_password_service.verify_password")
    def test_same_as_current_password(self, mock_verify):
        # Primera llamada (verify current): True
        # Segunda llamada (verify same): True
        mock_verify.return_value = True
        user = make_user()
        svc, _, _ = _make_service(user)

        result = svc.change(1, "SamePass1", "SamePass1")

        assert result.success is False
        assert result.error.code == "PASSWORD_SAME_AS_CURRENT"

    # ------------------------------------------------------------------
    # Password demasiado débil
    # ------------------------------------------------------------------

    @patch("app.modules.users.services.auth.change_password_service.verify_password")
    def test_weak_new_password(self, mock_verify):
        # Primera llamada (verify current): True, segunda (verify same): False
        mock_verify.side_effect = [True, False]
        user = make_user()
        svc, _, _ = _make_service(user)

        result = svc.change(1, "OldPass1", "weak")

        assert result.success is False
        assert result.error.code in ("VALIDATION_ERROR", "PASSWORD_TOO_WEAK")

    # ------------------------------------------------------------------
    # Input inválido
    # ------------------------------------------------------------------

    def test_empty_current_password(self):
        user = make_user()
        svc, _, _ = _make_service(user)

        result = svc.change(1, "", "NewSecure1")

        assert result.success is False
        assert result.error.code == "VALIDATION_ERROR"
