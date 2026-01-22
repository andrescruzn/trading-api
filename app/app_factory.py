# -*- coding: utf-8 -*-

# ======================================================================
# app/app_factory.py
# ======================================================================

# 1) Registro de modelos ORM (necesario para FKs)
import app.extensions.db.models_registry  # noqa: F401

from fastapi import FastAPI

from app.common.config import settings
from app.common.errors import register_error_handlers
from app.modules.users.rest import auth_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)

    # Routers
    app.include_router(auth_router)

    # ✅ Handlers globales (AuthException/JwtCodecError -> envelope)
    register_error_handlers(app)

    return app