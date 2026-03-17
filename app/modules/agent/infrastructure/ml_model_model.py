# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/infrastructure/ml_model_model.py
#
# Modelo SQLAlchemy para la tabla `models`.
#
# NOTA: La clase se llama MLModelORM para evitar:
#   - Colisión con la clase de dominio MLModel
#   - Ambigüedad visual (ModelModel sería confuso)
# ======================================================================

from sqlalchemy import BigInteger, Column, JSON, SmallInteger, String, Text, TIMESTAMP, text

from app.extensions.db import Base


class MLModelORM(Base):
    """Modelo SQLAlchemy para la tabla `models`."""

    __tablename__ = "models"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    version = Column(String(32), nullable=False)
    model_type = Column(String(32), nullable=False)
    feature_set_id = Column(BigInteger, nullable=True)
    artifact_uri = Column(String(512), nullable=True)
    status = Column(String(16), nullable=False, server_default=text("'active'"))
    meta = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
