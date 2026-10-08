# -*- coding: utf-8 -*-

# ======================================================================
# app/common/audit/audit_log_model.py
#
# Modelo SQLAlchemy para la tabla `audit_logs`.
#
# NOTAS:
# - Auditoría de eventos de negocio (usuario / bot). Distinta de las tablas
#   `http_audit_YYYY`, que registran cada request HTTP y se crean en runtime
#   (ver audit_table_factory.py).
# - Hoy ningún servicio escribe en esta tabla; el modelo existe para que el
#   esquema completo lo gestione Alembic.
# ======================================================================

from sqlalchemy import BigInteger, CheckConstraint, Column, ForeignKey, Index, JSON, String, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class AuditLogModel(Base):
    """Modelo SQLAlchemy para la tabla `audit_logs`."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_ts", "ts"),
        Index("idx_audit_logs_user_ts", "user_id", "ts"),
        Index("idx_audit_logs_bot_ts", "bot_id", "ts"),
        CheckConstraint("json_valid(`data`)", name="chk_audit_logs_data_json"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", name="fk_audit_logs_user"), nullable=True)
    bot_id = Column(BigInteger, ForeignKey("bots.id", name="fk_audit_logs_bot"), nullable=True)
    event_type = Column(String(32), nullable=False)
    ts = Column(TIMESTAMP(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    ip = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    data = Column(JSON, nullable=False)
