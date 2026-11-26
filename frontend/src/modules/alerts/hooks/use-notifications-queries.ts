import { useQuery } from '@tanstack/react-query';
import {
	listNotifications,
	type NotificationFilters,
} from '@/modules/alerts/api/notifications.api';

const NOTIFICATIONS_QUERY_KEY = ['notifications'] as const;

/** La campana consulta cada minuto (solo con la pestaña visible) y al volver a ella. */
const NOTIFICATIONS_REFETCH_MS = 60_000;

const DEFAULT_NOTIFICATIONS_LIMIT = 20;

function useNotificationsQuery(filters: NotificationFilters = {}) {
	const params = { limit: DEFAULT_NOTIFICATIONS_LIMIT, ...filters };
	return useQuery({
		queryKey: [...NOTIFICATIONS_QUERY_KEY, params],
		queryFn: () => listNotifications(params),
		refetchInterval: NOTIFICATIONS_REFETCH_MS,
		refetchOnWindowFocus: true,
	});
}

export {
	DEFAULT_NOTIFICATIONS_LIMIT,
	NOTIFICATIONS_QUERY_KEY,
	NOTIFICATIONS_REFETCH_MS,
	useNotificationsQuery,
};
