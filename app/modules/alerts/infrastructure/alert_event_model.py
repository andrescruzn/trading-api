# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/infrastructure/alert_event_model.py
#
# Modelo ORM para la tabla alert_events.
# ======================================================================

from __future__ import annotations

from sqlalchemy import BigInteger, Column, JSON, String, Text, TIMESTAMP
from sqlalchemy.sql import func

from app.extensions.db.base import Base


class AlertEventModel(Base):
    __tablename__ = "alert_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alert_rule_id = Column(BigInteger, nullable=True)
    user_id = Column(BigInteger, nullable=True)
    bot_id = Column(BigInteger, nullable=True)
    ts = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    severity = Column(String(16), nullable=False, default="info")
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    payload = Column(JSON, nullable=False)
    delivery_status = Column(String(16), nullable=False, default="pending")
