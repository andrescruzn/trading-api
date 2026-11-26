# app/modules/users/rest/__init__.py
# -*- coding: utf-8 -*-

from .audit import router as audit_router
from .auth import router as auth_router
from .telegram import router as telegram_link_router
from .users import router as users_router

__all__ = ["audit_router", "auth_router", "telegram_link_router", "users_router"]