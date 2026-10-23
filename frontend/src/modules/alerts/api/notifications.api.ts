import type { AlertSeverity } from '@/modules/alerts/api/alerts.api';
import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// ======================================================================

/** Un evento de alerta del usuario, tal como lo muestra la campana. */
type AppNotification = {
	id: number;
	/** UTC con offset (`+00:00`): `formatDateTime` lo pasa a la hora de Colombia. */
	ts: string | null;
	title: string;
	message: string | null;
	severity: AlertSeverity;
	bot_id: number | null;
	/** Posterior a la última vez que se abrió la campana (en cualquier dispositivo). */
	is_new: boolean;
};

type NotificationFeed = {
	items: AppNotification[];
	/** Todos los eventos nuevos, no solo los listados. */
	unread_count: number;
	seen_at: string | null;
};

type NotificationFilters = {
	limit?: number;
};

type NotificationsSeen = { seen_at: string | null };

// ======================================================================
// Notificaciones en la app (campana del header)
// ======================================================================

/** Últimos eventos de alerta del usuario autenticado + contador de no leídos. */
function listNotifications(filters: NotificationFilters = {}) {
	return api.get<NotificationFeed>('/notifications', filters);
}

/** Marca todo como visto: se guarda en la cuenta, así vale para todos los dispositivos. */
function markNotificationsSeen() {
	return api.post<NotificationsSeen>('/notifications/seen');
}

export type {
	AppNotification,
	NotificationFeed,
	NotificationFilters,
	NotificationsSeen,
};
export { listNotifications, markNotificationsSeen };
