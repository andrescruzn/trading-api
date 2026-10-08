# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/infrastructure/alert_rule_model.py
#
# Modelo ORM para la tabla alert_rules.
# ======================================================================

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, ForeignKey, Index, JSON, String, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db.base import Base, MYSQL_TABLE_OPTIONS


class AlertRuleModel(Base):
    __tablename__ = "alert_rules"
    __table_args__ = (
        Index("idx_alert_rules_user", "user_id"),
        Index("idx_alert_rules_bot", "bot_id"),
        CheckConstraint("json_valid(`channels`)", name="chk_alert_rules_channels_json"),
        CheckConstraint("json_valid(`rule_spec`)", name="chk_alert_rules_rule_spec_json"),
        CheckConstraint(
            "`rule_type` IN ('pnl', 'drawdown', 'signal', 'error', 'price')",
            name="chk_alert_rules_type",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", name="fk_alert_rules_user"), nullable=True)
    bot_id = Column(BigInteger, ForeignKey("bots.id", name="fk_alert_rules_bot"), nullable=True)
    name = Column(String(255), nullable=False)
    rule_type = Column(String(16), nullable=False)
    rule_spec = Column(JSON, nullable=False)
    channels = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("'1'"))
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
