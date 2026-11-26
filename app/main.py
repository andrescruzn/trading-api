# -*- coding: utf-8 -*-

# ======================================================================
# app/main.py
# Entry point (uvicorn app.main:app)
# ======================================================================

from app.app_factory import create_app

app = create_app()