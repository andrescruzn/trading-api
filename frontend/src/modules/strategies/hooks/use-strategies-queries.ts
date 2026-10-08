import { useQuery } from '@tanstack/react-query';
import { getStrategy, listStrategies } from '@/modules/strategies/api/strategies.api';

const STRATEGIES_QUERY_KEY = ['strategies'] as const;

function useStrategiesQuery() {
	return useQuery({
		queryKey: STRATEGIES_QUERY_KEY,
		queryFn: listStrategies,
		staleTime: 60 * 1000,
	});
}

function useStrategyQuery(id: number | null) {
	return useQuery({
		queryKey: [...STRATEGIES_QUERY_KEY, id],
		queryFn: () => getStrategy(id as number),
		enabled: !!id,
	});
}

export { STRATEGIES_QUERY_KEY, useStrategiesQuery, useStrategyQuery };
