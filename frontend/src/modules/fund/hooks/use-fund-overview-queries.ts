import { useQuery } from '@tanstack/react-query';
import {
	getFundOverview,
	getMySummary,
} from '@/modules/fund/api/fund-overview.api';

const FUND_OVERVIEW_QUERY_KEY = ['fund-overview'] as const;
const MY_SUMMARY_QUERY_KEY = ['fund-my-summary'] as const;

const REFETCH_MS = 60_000;

/** Solo staff: el backend responde 403 a un inversor. */
function useFundOverviewQuery() {
	return useQuery({
		queryKey: FUND_OVERVIEW_QUERY_KEY,
		queryFn: getFundOverview,
		refetchInterval: REFETCH_MS,
	});
}

function useMySummaryQuery() {
	return useQuery({
		queryKey: MY_SUMMARY_QUERY_KEY,
		queryFn: getMySummary,
		refetchInterval: REFETCH_MS,
	});
}

export {
	FUND_OVERVIEW_QUERY_KEY,
	MY_SUMMARY_QUERY_KEY,
	useFundOverviewQuery,
	useMySummaryQuery,
};
