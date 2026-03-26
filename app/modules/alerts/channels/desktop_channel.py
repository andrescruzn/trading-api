# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/desktop_channel.py
#
# Canal de notificación Desktop (plyer — macOS/Windows/Linux).
# Solo se activa si DESKTOP_NOTIFICATIONS_ENABLED=true en settings.
# ======================================================================

from __future__ import annotations

import logging

from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_rule_entity import AlertRule

logger = logging.getLogger(__name__)


class DesktopChannel:
    """
    Canal Desktop — notificaciones nativas del SO.

    Estrategia:
    1. Intenta con plyer (requiere: pip install plyer pyobjus en macOS)
    2. Fallback macOS: osascript (built-in, sin dependencias)
    3. Si ninguno funciona, retorna False silenciosamente.

    Solo activo si DESKTOP_NOTIFICATIONS_ENABLED=true en settings.
    """

    def send(self, event: AlertEvent, rule: AlertRule) -> bool:
        title = f"[{event.severity.upper()}] {event.title}"
        message = event.message or f"Regla: {rule.name}"

        # Intento 1: plyer (funciona en Windows, Linux y macOS con pyobjus)
        try:
            from plyer import notification  # type: ignore
            notification.notify(
                title=title,
                message=message,
                app_name="Trading AI",
                timeout=10,
            )
            return True
        except ImportError:
            pass
        except NotImplementedError:
            pass
        except Exception as exc:
            logger.warning("DesktopChannel plyer error: %s — intentando osascript", exc)

        # Intento 2: osascript (macOS nativo, sin dependencias)
        try:
            import subprocess
            import sys
            if sys.platform == "darwin":
                safe_title = title.replace('"', '\\"')
                safe_msg = message.replace('"', '\\"')
                subprocess.run(
                    ["osascript", "-e",
                     f'display notification "{safe_msg}" with title "{safe_title}"'],
                    check=True, capture_output=True, timeout=5,
                )
                return True
        except Exception as exc:
            logger.error("DesktopChannel osascript error: %s", exc)

        return False
