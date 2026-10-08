# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/infrastructure/alert_event_model.py
#
# Modelo ORM para la tabla alert_events.
#
# NOTA: el índice de `alert_rule_id` lo crea MySQL solo, con el nombre de su
# FK (`fk_alert_events_rule`): no se declara.
# ======================================================================

from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, Column, ForeignKey, Index, JSON, String, Text, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db.base import Base, MYSQL_TABLE_OPTIONS


class AlertEventModel(Base):
    __tablename__ = "alert_events"
    __table_args__ = (
        Index("idx_alert_events_ts", "ts"),
        Index("idx_alert_events_user_ts", "user_id", "ts"),
        Index("idx_alert_events_bot_ts", "bot_id", "ts"),
        Index("idx_alert_events_delivery_ts", "delivery_status", "ts"),
        CheckConstraint(
            "`delivery_status` IN ('pending', 'sent', 'failed')",
            name="chk_alert_events_delivery",
        ),
        CheckConstraint("json_valid(`payload`)", name="chk_alert_events_payload_json"),
        CheckConstraint(
            "`severity` IN ('info', 'warning', 'critical')",
            name="chk_alert_events_severity",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alert_rule_id = Column(
        BigInteger,
        ForeignKey("alert_rules.id", name="fk_alert_events_rule", ondelete="SET NULL"),
        nullable=True,
    )
    user_id = Column(BigInteger, ForeignKey("users.id", name="fk_alert_events_user"), nullable=True)
    bot_id = Column(BigInteger, ForeignKey("bots.id", name="fk_alert_events_bot"), nullable=True)
    ts = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    severity = Column(String(16), nullable=False, default="info", server_default=text("'info'"))
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    payload = Column(JSON, nullable=False)
    delivery_status = Column(
        String(16),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
