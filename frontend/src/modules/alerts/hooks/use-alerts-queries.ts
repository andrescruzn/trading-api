import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
	type AlertEventFilters,
	listAlertEventsPage,
	listAlertRules,
} from '@/modules/alerts/api/alerts.api';
import type { PageParams } from '@/modules/shared/types/api';

const ALERT_RULES_QUERY_KEY = ['alert-rules'] as const;
const ALERT_EVENTS_QUERY_KEY = ['alert-events'] as const;

function useAlertRulesQuery() {
	return useQuery({
		queryKey: ALERT_RULES_QUERY_KEY,
		queryFn: listAlertRules,
	});
}

/** Una página del historial de eventos (paginación en el servidor). */
function useAlertEventsPageQuery(filters: AlertEventFilters, page: PageParams) {
	return useQuery({
		queryKey: [...ALERT_EVENTS_QUERY_KEY, 'page', filters, page],
		queryFn: () => listAlertEventsPage(filters, page),
		placeholderData: keepPreviousData,
	});
}

export {
	ALERT_EVENTS_QUERY_KEY,
	ALERT_RULES_QUERY_KEY,
	useAlertEventsPageQuery,
	useAlertRulesQuery,
};
