# -*- coding: utf-8 -*-

# ======================================================================
# tests/users/test_get_me_service.py
# ======================================================================

from unittest.mock import MagicMock

import pytest
from tests.conftest import make_user, make_mock_repo
from app.modules.users.services.auth.get_me_service import GetMeService


def _make_role_row(code: str = "user", name: str = "Usuario") -> MagicMock:
    """Simula el mappings().first() de la query de roles."""
    row = MagicMock()
    row.__getitem__ = lambda self, key: {"code": code, "name": name}[key]
    return row


def _make_service(user=None, role_row=None):
    repo = make_mock_repo(user)
    session = MagicMock()
    # Simula session.execute(...).mappings().first()
    session.execute.return_value.mappings.return_value.first.return_value = role_row
    return GetMeService(repo=repo, session=session), repo, session


class TestGetMeService:

    # ------------------------------------------------------------------
    # Casos exitosos
    # ------------------------------------------------------------------

    def test_get_returns_user_profile_with_role_from_db(self):
        user = make_user(id=1, email="user@test.com", full_name="Ana López", role_id=1)
        role = _make_role_row(code="user", name="Usuario")
        svc, _, _ = _make_service(user, role)

        result = svc.get(user_id=1)

        assert result.success is True
        assert result.data.id == 1
        assert result.data.email == "user@test.com"
        assert result.data.full_name == "Ana López"
        assert result.data.role_id == 1
        assert result.data.role_code == "user"
        assert result.data.role_name == "Usuario"
        assert result.data.status == "active"

    def test_get_admin_role_from_db(self):
        user = make_user(role_id=2)
        role = _make_role_row(code="admin", name="Administrador")
        svc, _, _ = _make_service(user, role)

        result = svc.get(user_id=1)

        assert result.success is True
        assert result.data.role_code == "admin"
        assert result.data.role_name == "Administrador"

    def test_get_with_no_full_name(self):
        user = make_user(full_name=None)
        role = _make_role_row()
        svc, _, _ = _make_service(user, role)

        result = svc.get(user_id=1)

        assert result.success is True
        assert result.data.full_name is None

    def test_get_queries_db_with_correct_role_id(self):
        user = make_user(role_id=2)
        role = _make_role_row(code="admin", name="Administrador")
        svc, _, session = _make_service(user, role)

        svc.get(user_id=1)

        # Verificar que se hizo query a la tabla roles
        call_args = session.execute.call_args
        assert call_args is not None
        query_str = str(call_args[0][0])
        assert "roles" in query_str.lower()

    def test_get_passes_user_id_to_repo(self):
        user = make_user(id=42)
        role = _make_role_row()
        svc, repo, _ = _make_service(user, role)

        svc.get(user_id=42)

        repo.get_by_id.assert_called_once_with(42)

    # ------------------------------------------------------------------
    # Casos de error
    # ------------------------------------------------------------------

    def test_get_user_not_found(self):
        svc, _, _ = _make_service(user=None, role_row=None)

        result = svc.get(user_id=99)

        assert result.success is False
        assert result.error.code == "USER_NOT_FOUND"
        assert result.error.http_status == 404

    def test_get_role_not_found_in_db(self):
        """Si el role_id del usuario no existe en la tabla roles."""
        user = make_user(role_id=99)
        svc, _, _ = _make_service(user, role_row=None)

        result = svc.get(user_id=1)

        assert result.success is False
        assert result.error.code == "ROLE_NOT_FOUND"
        assert result.error.http_status == 500

    def test_get_converts_user_id_to_int(self):
        user = make_user(id=5)
        role = _make_role_row()
        svc, repo, _ = _make_service(user, role)

        svc.get(user_id="5")  # type: ignore

        repo.get_by_id.assert_called_once_with(5)
