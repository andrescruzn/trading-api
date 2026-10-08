# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/infrastructure/model_run_model.py
#
# Modelo SQLAlchemy para la tabla `model_runs`.
# ======================================================================

from sqlalchemy import BigInteger, CheckConstraint, Column, ForeignKey, Index, JSON, String, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class ModelRunORM(Base):
    """Modelo SQLAlchemy para la tabla `model_runs`."""

    __tablename__ = "model_runs"
    __table_args__ = (
        Index("idx_model_runs_model", "model_id", "started_at"),
        Index("idx_model_runs_dataset", "dataset_id"),
        CheckConstraint("json_valid(`metrics`)", name="chk_model_runs_metrics_json"),
        CheckConstraint("json_valid(`params`)", name="chk_model_runs_params_json"),
        CheckConstraint(
            "`status` IN ('running', 'success', 'failed')",
            name="chk_model_runs_status",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    model_id = Column(
        BigInteger,
        ForeignKey("models.id", name="fk_model_runs_model", ondelete="CASCADE"),
        nullable=False,
    )
    dataset_id = Column(
        BigInteger,
        ForeignKey("datasets.id", name="fk_model_runs_dataset"),
        nullable=True,
    )
    started_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    finished_at = Column(TIMESTAMP(fsp=6), nullable=True)
    status = Column(String(16), nullable=False, server_default=text("'running'"))
    metrics = Column(JSON, nullable=False)
    params = Column(JSON, nullable=False)
    logs_uri = Column(String(512), nullable=True)
