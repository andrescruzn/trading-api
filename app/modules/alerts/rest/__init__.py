# -*- coding: utf-8 -*-
from app.modules.alerts.rest.alert_rules.routes import router as alert_rules_router
from app.modules.alerts.rest.alert_events.routes import router as alert_events_router
from app.modules.alerts.rest.admin_routes import router as alerts_admin_router

__all__ = ["alert_rules_router", "alert_events_router", "alerts_admin_router"]
