# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/infrastructure/feature_set_model.py
#
# Modelo SQLAlchemy para la tabla `feature_sets`.
# ======================================================================

from sqlalchemy import BigInteger, CheckConstraint, Column, JSON, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class FeatureSetModel(Base):
    """Modelo SQLAlchemy para la tabla `feature_sets`."""

    __tablename__ = "feature_sets"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_feature_sets_name_version"),
        CheckConstraint("json_valid(`spec`)", name="chk_feature_sets_spec_json"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    version = Column(String(32), nullable=False, server_default=text("'1.0.0'"))
    description = Column(Text, nullable=True)
    spec = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
