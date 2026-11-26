# -*- coding: utf-8 -*-

# ======================================================================
# tests/common/security/test_security_headers.py
#
# Headers de seguridad y respuestas de la API headless (sin páginas HTML).
# ======================================================================

from __future__ import annotations


class TestSecurityHeaders:

    def test_api_endpoint_has_restrictive_csp(self, client):
        res = client.get("/health")
        assert "default-src 'none'" in res.headers.get("content-security-policy", "")

    def test_docs_allow_swagger_cdn(self, client):
        res = client.get("/docs")
        assert "cdn.jsdelivr.net" in res.headers.get("content-security-policy", "")

    def test_x_frame_options_deny(self, client):
        res = client.get("/health")
        assert res.headers.get("x-frame-options") == "DENY"

    def test_nosniff_header(self, client):
        res = client.get("/health")
        assert res.headers.get("x-content-type-options") == "nosniff"


class TestHeadlessApi:

    def test_root_is_json_404(self, client):
        res = client.get("/")
        assert res.status_code == 404
        body = res.json()
        assert body["errorCode"] == 404
        assert "msg" in body and "data" in body

    def test_old_web_pages_are_gone(self, client):
        res = client.get("/login")
        assert res.status_code == 404

    def test_protected_endpoint_requires_auth(self, client):
        res = client.get("/api/users/me")
        assert res.status_code == 401
        assert res.json()["errorCode"] == 401

    def test_validation_error_uses_envelope(self, client):
        res = client.post("/api/users/login", json={"email": "no-es-un-correo"})
        assert res.status_code == 422
        body = res.json()
        assert body["errorCode"] == 422
        assert isinstance(body["data"], list) and body["data"]
