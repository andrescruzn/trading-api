import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
	type AuditEventsFilters,
	listAuditEvents,
} from '@/modules/auth/api/audit.api';

const AUDIT_EVENTS_QUERY_KEY = ['audit-logs'] as const;

/** Solo admin. Paginado en el servidor: la página y los filtros van en la key. */
function useAuditEventsQuery(
	filters: AuditEventsFilters,
	options: { enabled?: boolean } = {},
) {
	return useQuery({
		queryKey: [...AUDIT_EVENTS_QUERY_KEY, filters],
		queryFn: () => listAuditEvents(filters),
		placeholderData: keepPreviousData,
		enabled: options.enabled ?? true,
	});
}

export { AUDIT_EVENTS_QUERY_KEY, useAuditEventsQuery };
