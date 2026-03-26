# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/infrastructure/alert_rule_model.py
#
# Modelo ORM para la tabla alert_rules.
# ======================================================================

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, JSON, String, TIMESTAMP
from sqlalchemy.sql import func

from app.extensions.db.base import Base


class AlertRuleModel(Base):
    __tablename__ = "alert_rules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    bot_id = Column(BigInteger, nullable=True)
    name = Column(String(255), nullable=False)
    rule_type = Column(String(16), nullable=False)
    rule_spec = Column(JSON, nullable=False)
    channels = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
