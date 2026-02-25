# -*- coding: utf-8 -*-

# ======================================================================
# tests/common/audit/test_audit_sanitizer.py
#
# Tests unitarios para audit_sanitizer.py.
# Sin I/O — solo lógica de transformación de dicts.
# ======================================================================

import json

import pytest

from app.common.audit.audit_sanitizer import sanitize_request, sanitize_response

_REDACTED = "***REDACTED***"


# ======================================================================
# sanitize_request
# ======================================================================

class TestSanitizeRequest:

    def test_empty_bytes_returns_none(self):
        assert sanitize_request(b"") is None

    def test_non_json_returns_none(self):
        assert sanitize_request(b"not json at all") is None

    def test_html_returns_none(self):
        assert sanitize_request(b"<html><body>hello</body></html>") is None

    def test_json_array_returns_none(self):
        # Root no es dict → None
        assert sanitize_request(b'[1, 2, 3]') is None

    def test_clean_payload_passes_through(self):
        body = json.dumps({"email": "test@example.com"}).encode()
        result = sanitize_request(body)
        assert result == {"email": "test@example.com"}

    def test_password_is_redacted(self):
        body = json.dumps({"email": "user@x.com", "password": "secret123"}).encode()
        result = sanitize_request(body)
        assert result is not None
        assert result["password"] == _REDACTED
        assert result["email"] == "user@x.com"

    def test_password_key_is_preserved_after_redaction(self):
        # La clave debe seguir presente aunque el valor sea redacted
        body = json.dumps({"password": "secret"}).encode()
        result = sanitize_request(body)
        assert result is not None
        assert "password" in result

    def test_current_password_is_redacted(self):
        body = json.dumps({"current_password": "old", "new_password": "new"}).encode()
        result = sanitize_request(body)
        assert result is not None
        assert result["current_password"] == _REDACTED
        assert result["new_password"] == _REDACTED

    def test_otp_code_is_redacted(self):
        body = json.dumps({"otp_code": "123456"}).encode()
        result = sanitize_request(body)
        assert result is not None
        assert result["otp_code"] == _REDACTED

    def test_token_in_request_is_redacted(self):
        body = json.dumps({"token": "some-token"}).encode()
        result = sanitize_request(body)
        assert result is not None
        assert result["token"] == _REDACTED

    def test_non_sensitive_fields_untouched(self):
        body = json.dumps({"email": "x@x.com", "remember_me": True}).encode()
        result = sanitize_request(body)
        assert result is not None
        assert result["email"] == "x@x.com"
        assert result["remember_me"] is True


# ======================================================================
# sanitize_response
# ======================================================================

class TestSanitizeResponse:

    def test_empty_bytes_returns_none(self):
        assert sanitize_response(b"") is None

    def test_html_returns_none(self):
        assert sanitize_response(b"<html>...</html>") is None

    def test_non_json_returns_none(self):
        assert sanitize_response(b"plain text response") is None

    def test_json_array_returns_none(self):
        assert sanitize_response(b'[1, 2, 3]') is None

    def test_clean_response_passes_through(self):
        body = json.dumps({"msg": "OK", "errorCode": 200, "data": {}}).encode()
        result = sanitize_response(body)
        assert result is not None
        assert result["msg"] == "OK"
        assert result["errorCode"] == 200

    def test_token_in_root_is_redacted(self):
        body = json.dumps({"token": "jwt-here", "msg": "OK"}).encode()
        result = sanitize_response(body)
        assert result is not None
        assert result["token"] == _REDACTED

    def test_access_token_in_root_is_redacted(self):
        body = json.dumps({"access_token": "jwt-here"}).encode()
        result = sanitize_response(body)
        assert result is not None
        assert result["access_token"] == _REDACTED

    def test_token_inside_data_is_redacted(self):
        body = json.dumps({"msg": "OK", "data": {"token": "secret-jwt"}}).encode()
        result = sanitize_response(body)
        assert result is not None
        assert result["data"]["token"] == _REDACTED

    def test_access_token_inside_data_is_redacted(self):
        body = json.dumps({"data": {"access_token": "abc"}}).encode()
        result = sanitize_response(body)
        assert result is not None
        assert result["data"]["access_token"] == _REDACTED

    def test_data_non_dict_is_preserved(self):
        # Si data es lista u otro tipo, no crashea
        body = json.dumps({"msg": "OK", "data": [1, 2, 3]}).encode()
        result = sanitize_response(body)
        assert result is not None
        assert result["data"] == [1, 2, 3]
