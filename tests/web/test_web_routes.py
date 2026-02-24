# -*- coding: utf-8 -*-

# ======================================================================
# tests/web/test_web_routes.py
#
# Tests para las rutas de páginas web.
# ======================================================================

import pytest
from fastapi.testclient import TestClient
from app.app_factory import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app, raise_server_exceptions=False, follow_redirects=False) as c:
        yield c


class TestRootRedirect:

    def test_root_redirects_to_login_without_cookie(self, client):
        res = client.get("/")
        assert res.status_code in (301, 302)
        assert "/login" in res.headers.get("location", "")

    def test_root_redirects_to_dashboard_with_invalid_cookie(self, client):
        # Cookie inválida → /login
        res = client.get("/", cookies={"access_token": "invalid.jwt.token"})
        assert res.status_code in (301, 302)
        assert "/login" in res.headers.get("location", "")


class TestLoginPage:

    def test_login_page_returns_200(self, client):
        res = client.get("/login")
        assert res.status_code == 200

    def test_login_page_contains_form(self, client):
        res = client.get("/login")
        assert "form" in res.text.lower()
        assert "email" in res.text.lower()

    def test_login_page_has_security_headers(self, client):
        res = client.get("/login")
        assert "x-frame-options" in res.headers
        assert "x-content-type-options" in res.headers
        assert "content-security-policy" in res.headers

    def test_login_page_with_valid_cookie_redirects_to_dashboard(self, client):
        # Cookie inválida (sin DB real) → sigue en /login
        res = client.get("/login", cookies={"access_token": "invalid"})
        assert res.status_code == 200


class TestDashboardPage:

    def test_dashboard_without_cookie_redirects_to_login(self, client):
        res = client.get("/dashboard")
        assert res.status_code in (301, 302)
        assert "/login" in res.headers.get("location", "")

    def test_dashboard_with_invalid_cookie_redirects_to_login(self, client):
        res = client.get("/dashboard", cookies={"access_token": "bad.token"})
        assert res.status_code in (301, 302)
        assert "/login" in res.headers.get("location", "")


class TestProfilePage:

    def test_profile_without_cookie_redirects_to_login(self, client):
        res = client.get("/profile")
        assert res.status_code in (301, 302)
        assert "/login" in res.headers.get("location", "")

    def test_profile_with_invalid_cookie_redirects_to_login(self, client):
        res = client.get("/profile", cookies={"access_token": "bad.token"})
        assert res.status_code in (301, 302)
        assert "/login" in res.headers.get("location", "")


class TestSecurityHeaders:

    def test_api_endpoint_has_restrictive_csp(self, client):
        res = client.get("/health")
        csp = res.headers.get("content-security-policy", "")
        assert "default-src 'none'" in csp or "default-src 'self'" in csp

    def test_x_frame_options_deny(self, client):
        res = client.get("/login")
        assert res.headers.get("x-frame-options") == "DENY"

    def test_nosniff_header(self, client):
        res = client.get("/login")
        assert res.headers.get("x-content-type-options") == "nosniff"
