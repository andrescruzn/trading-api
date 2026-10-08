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

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    JSON,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class MLModelORM(Base):
    """Modelo SQLAlchemy para la tabla `models`."""

    __tablename__ = "models"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_models_name_version"),
        Index("idx_models_status", "status"),
        Index("idx_models_feature_set", "feature_set_id"),
        CheckConstraint("json_valid(`meta`)", name="chk_models_meta_json"),
        CheckConstraint(
            "`model_type` IN ('xgboost', 'lightgbm', 'sklearn', 'nn')",
            name="chk_models_model_type",
        ),
        CheckConstraint(
            "`status` IN ('active', 'deprecated', 'archived')",
            name="chk_models_status",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    version = Column(String(32), nullable=False)
    model_type = Column(String(32), nullable=False)
    feature_set_id = Column(
        BigInteger,
        ForeignKey("feature_sets.id", name="fk_models_feature_set"),
        nullable=True,
    )
    artifact_uri = Column(String(512), nullable=True)
    status = Column(String(16), nullable=False, server_default=text("'active'"))
    meta = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
