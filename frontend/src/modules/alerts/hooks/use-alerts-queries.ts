import { useQuery } from '@tanstack/react-query';
import {
	type AlertEventFilters,
	listAlertEvents,
	listAlertRules,
} from '@/modules/alerts/api/alerts.api';

const ALERT_RULES_QUERY_KEY = ['alert-rules'] as const;
const ALERT_EVENTS_QUERY_KEY = ['alert-events'] as const;

function useAlertRulesQuery() {
	return useQuery({
		queryKey: ALERT_RULES_QUERY_KEY,
		queryFn: listAlertRules,
	});
}

function useAlertEventsQuery(filters: AlertEventFilters = {}) {
	return useQuery({
		queryKey: [...ALERT_EVENTS_QUERY_KEY, filters],
		queryFn: () => listAlertEvents(filters),
	});
}

export {
	ALERT_EVENTS_QUERY_KEY,
	ALERT_RULES_QUERY_KEY,
	useAlertEventsQuery,
	useAlertRulesQuery,
};
