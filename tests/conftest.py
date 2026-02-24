# -*- coding: utf-8 -*-

# ======================================================================
# tests/conftest.py
#
# Fixtures compartidos para todos los tests.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.app_factory import create_app
from app.modules.users.domain.user_entity import User


# ======================================================================
# App / HTTP client
# ======================================================================

@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ======================================================================
# User entity factory
# ======================================================================

def make_user(
    id: int = 1,
    email: str = "test@example.com",
    password_hash: str = "$2b$12$fixed_hash_for_tests",
    role_id: int = 1,
    status: str = "active",
    full_name: Optional[str] = "Test User",
    failed_attempts: int = 0,
    login_locked_until: Optional[datetime] = None,
    token_current_jti: Optional[str] = None,
    otp_code: Optional[str] = None,
    otp_expires_at: Optional[datetime] = None,
    last_login_at: Optional[datetime] = None,
) -> User:
    """Factory de entidad User para tests."""
    return User(
        id=id,
        email=email,
        password_hash=password_hash,
        role_id=role_id,
        status=status,
        full_name=full_name,
        failed_attempts=failed_attempts,
        login_locked_until=login_locked_until,
        token_current_jti=token_current_jti,
        otp_code=otp_code,
        otp_expires_at=otp_expires_at,
        last_login_at=last_login_at,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


# ======================================================================
# Mock repository factory
# ======================================================================

def make_mock_repo(user: Optional[User] = None) -> MagicMock:
    """Crea un mock del repositorio con un usuario opcional."""
    repo = MagicMock()
    repo.get_by_id.return_value = user
    repo.get_by_email.return_value = user
    repo.update.return_value = None
    return repo


# ======================================================================
# Mock session
# ======================================================================

@pytest.fixture
def mock_session():
    session = MagicMock()
    session.commit.return_value = None
    return session
