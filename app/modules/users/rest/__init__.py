# app/modules/users/rest/__init__.py
# -*- coding: utf-8 -*-

from .auth import router as auth_router
from .telegram import router as telegram_link_router
from .users import router as users_router

__all__ = ["auth_router", "telegram_link_router", "users_router"]