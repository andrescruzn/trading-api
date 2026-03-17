# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/infrastructure/model_run_model.py
#
# Modelo SQLAlchemy para la tabla `model_runs`.
# ======================================================================

from sqlalchemy import BigInteger, Column, JSON, String, Text, TIMESTAMP, text

from app.extensions.db import Base


class ModelRunORM(Base):
    """Modelo SQLAlchemy para la tabla `model_runs`."""

    __tablename__ = "model_runs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    model_id = Column(BigInteger, nullable=False)
    dataset_id = Column(BigInteger, nullable=True)
    started_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    finished_at = Column(TIMESTAMP(6), nullable=True)
    status = Column(String(16), nullable=False, server_default=text("'running'"))
    metrics = Column(JSON, nullable=False)
    params = Column(JSON, nullable=False)
    logs_uri = Column(String(512), nullable=True)
