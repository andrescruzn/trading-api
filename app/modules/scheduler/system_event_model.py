# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/scheduler/system_event_model.py
#
# Modelo SQLAlchemy para la tabla `system_events`.
#
# NOTAS:
# - Eventos técnicos de los componentes (market_data, execution, scheduler,
#   api) con nivel info | warning | error.
# - Hoy ningún servicio escribe en esta tabla; el modelo existe para que el
#   esquema completo lo gestione Alembic.
# ======================================================================

from sqlalchemy import BigInteger, CheckConstraint, Column, Index, JSON, String, Text, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class SystemEventModel(Base):
    """Modelo SQLAlchemy para la tabla `system_events`."""

    __tablename__ = "system_events"
    __table_args__ = (
        Index("idx_system_events_ts", "ts"),
        Index("idx_system_events_component_ts", "component", "ts"),
        CheckConstraint(
            "`component` IN ('market_data', 'execution', 'scheduler', 'api')",
            name="chk_system_events_component",
        ),
        CheckConstraint(
            "`level` IN ('info', 'warning', 'error')",
            name="chk_system_events_level",
        ),
        CheckConstraint("json_valid(`payload`)", name="chk_system_events_payload_json"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    component = Column(String(32), nullable=False)
    event_type = Column(String(32), nullable=False)
    ts = Column(TIMESTAMP(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    level = Column(String(16), nullable=False, server_default=text("'info'"))
    message = Column(Text, nullable=True)
    payload = Column(JSON, nullable=False)
