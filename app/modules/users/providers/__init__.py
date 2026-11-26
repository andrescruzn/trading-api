# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/providers/__init__.py
#
# Barrel exports para providers del módulo users.
#
# PATRÓN: Factory + Dependency Injection
# ======================================================================

from .auth_provider import AuthServiceFactory, get_auth_factory

__all__ = [
    "AuthServiceFactory",
    "get_auth_factory",
]
