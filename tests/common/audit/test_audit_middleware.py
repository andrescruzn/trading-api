# -*- coding: utf-8 -*-

# ======================================================================
# tests/common/audit/test_audit_middleware.py
#
# Tests de integración para AuditMiddleware.
# Usa TestClient con una mini-app FastAPI y mock del AuditRepository.
# ======================================================================

from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.common.audit.audit_middleware import AuditMiddleware
from app.common.audit.audit_repository import AuditRepository


# ======================================================================
# Helpers para construir mini-app de test
# ======================================================================

def make_test_app(mock_repo: AuditRepository) -> FastAPI:
    """
    Crea una mini-app FastAPI con AuditMiddleware y endpoints de prueba.
    """
    app = FastAPI()
    app.add_middleware(AuditMiddleware, repository=mock_repo)

    @app.post("/users/login")
    async def login():
        return JSONResponse({"msg": "OK", "errorCode": 200, "data": {}})

    @app.post("/users/logout")
    async def logout():
        return JSONResponse({"msg": "OK", "errorCode": 200, "data": {}})

    @app.get("/users/me")
    async def get_me():
        return JSONResponse({"msg": "OK", "errorCode": 200, "data": {"user_id": 1}})

    @app.get("/health")
    async def health():
        return JSONResponse({"status": "ok"})

    @app.get("/some/endpoint")
    async def generic():
        return JSONResponse({"msg": "generic"})

    return app


@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=AuditRepository)
    repo.insert.return_value = None
    return repo


@pytest.fixture
def client(mock_repo):
    app = make_test_app(mock_repo)
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ======================================================================
# Tests
# ======================================================================

class TestAuditMiddlewareSkipsExcludedPaths:

    def test_skips_health_endpoint(self, client, mock_repo):
        client.get("/health")
        # Esperar a que el hilo daemon termine (puede tardar < 100ms)
        time.sleep(0.05)
        mock_repo.insert.assert_not_called()

    def test_skips_static_paths(self, mock_repo):
        app = make_test_app(mock_repo)
        # No montamos static real — solo verificamos que la lógica de skip
        # no invoca insert para paths que empiezan con /static/
        # Probamos directo con el middleware sin TestClient para static

        # Alternativa: verificamos via /static/ → 404 pero sin insert
        with TestClient(app, raise_server_exceptions=False) as c:
            c.get("/static/some/file.css")
            time.sleep(0.05)
            mock_repo.insert.assert_not_called()


class TestAuditMiddlewareInsertsForNormalRequests:

    def test_insert_called_for_normal_request(self, client, mock_repo):
        client.get("/some/endpoint")
        time.sleep(0.1)
        mock_repo.insert.assert_called_once()

    def test_insert_called_for_post_request(self, client, mock_repo):
        client.post("/users/login", json={"email": "x@x.com", "password": "secret"})
        time.sleep(0.1)
        mock_repo.insert.assert_called_once()

    def test_response_body_preserved(self, client, mock_repo):
        """El body que recibe el cliente no debe cambiar."""
        response = client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["msg"] == "OK"
        assert data["data"]["user_id"] == 1

    def test_status_code_preserved(self, client, mock_repo):
        response = client.get("/some/endpoint")
        assert response.status_code == 200


class TestAuditMiddlewareEventTypes:

    def test_event_type_login_password_when_password_in_payload(self, client, mock_repo):
        client.post("/users/login", json={"email": "x@x.com", "password": "secret"})
        time.sleep(0.1)
        mock_repo.insert.assert_called_once()
        kwargs = mock_repo.insert.call_args.kwargs
        assert kwargs["event_type"] == "LOGIN_PASSWORD"

    def test_event_type_login_otp_when_no_password_in_payload(self, client, mock_repo):
        client.post("/users/login", json={"email": "x@x.com", "otp_code": "123456"})
        time.sleep(0.1)
        mock_repo.insert.assert_called_once()
        kwargs = mock_repo.insert.call_args.kwargs
        assert kwargs["event_type"] == "LOGIN_OTP_REQUEST"

    def test_event_type_logout(self, client, mock_repo):
        client.post("/users/logout")
        time.sleep(0.1)
        mock_repo.insert.assert_called_once()
        kwargs = mock_repo.insert.call_args.kwargs
        assert kwargs["event_type"] == "LOGOUT"

    def test_event_type_get_profile(self, client, mock_repo):
        client.get("/users/me")
        time.sleep(0.1)
        mock_repo.insert.assert_called_once()
        kwargs = mock_repo.insert.call_args.kwargs
        assert kwargs["event_type"] == "GET_PROFILE"

    def test_event_type_fallback_for_generic_endpoint(self, client, mock_repo):
        client.get("/some/endpoint")
        time.sleep(0.1)
        mock_repo.insert.assert_called_once()
        kwargs = mock_repo.insert.call_args.kwargs
        assert kwargs["event_type"] == "HTTP_REQUEST"


class TestAuditMiddlewarePayloadSanitization:

    def test_password_redacted_in_request_payload(self, client, mock_repo):
        client.post("/users/login", json={"email": "x@x.com", "password": "super_secret"})
        time.sleep(0.1)
        mock_repo.insert.assert_called_once()
        kwargs = mock_repo.insert.call_args.kwargs
        req = kwargs.get("request_payload", {})
        assert req is not None
        assert req.get("password") == "***REDACTED***"

    def test_email_not_redacted(self, client, mock_repo):
        client.post("/users/login", json={"email": "user@x.com", "password": "secret"})
        time.sleep(0.1)
        kwargs = mock_repo.insert.call_args.kwargs
        req = kwargs.get("request_payload", {})
        assert req is not None
        assert req.get("email") == "user@x.com"


class TestAuditMiddlewareUserIdExtraction:

    def test_user_id_none_without_jwt_cookie(self, client, mock_repo):
        client.get("/some/endpoint")
        time.sleep(0.1)
        kwargs = mock_repo.insert.call_args.kwargs
        assert kwargs["user_id"] is None

    def test_user_id_none_with_invalid_jwt(self, client, mock_repo):
        client.get("/some/endpoint", cookies={"access_token": "bad.token.here"})
        time.sleep(0.1)
        kwargs = mock_repo.insert.call_args.kwargs
        assert kwargs["user_id"] is None


class TestAuditMiddlewareResilience:

    def test_audit_error_does_not_break_request(self, mock_repo):
        """Si repo.insert falla, el response al cliente sigue siendo correcto."""
        mock_repo.insert.side_effect = Exception("DB connection lost")

        app = make_test_app(mock_repo)
        with TestClient(app, raise_server_exceptions=True) as c:
            response = c.get("/some/endpoint")
            # El hilo daemon puede fallar silenciosamente sin afectar response
            assert response.status_code == 200

    def test_insert_receives_duration_ms(self, client, mock_repo):
        client.get("/some/endpoint")
        time.sleep(0.1)
        kwargs = mock_repo.insert.call_args.kwargs
        assert "duration_ms" in kwargs
        assert isinstance(kwargs["duration_ms"], int)
        assert kwargs["duration_ms"] >= 0

    def test_insert_receives_method_and_path(self, client, mock_repo):
        client.get("/some/endpoint")
        time.sleep(0.1)
        kwargs = mock_repo.insert.call_args.kwargs
        assert kwargs["method"] == "GET"
        assert kwargs["path"] == "/some/endpoint"

    def test_insert_receives_status_code(self, client, mock_repo):
        client.get("/some/endpoint")
        time.sleep(0.1)
        kwargs = mock_repo.insert.call_args.kwargs
        assert kwargs["status_code"] == 200
