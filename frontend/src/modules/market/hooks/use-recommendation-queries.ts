import { useQuery } from '@tanstack/react-query';
import { getLatestMarketRecommendation } from '@/modules/market/api/recommendations.api';

const RECOMMENDATIONS_QUERY_KEY = ['market-recommendations'] as const;

/** Solo cambia cuando alguien pide recomendaciones nuevas (se invalida). */
function useLatestRecommendationQuery() {
	return useQuery({
		queryKey: [...RECOMMENDATIONS_QUERY_KEY, 'latest'],
		queryFn: getLatestMarketRecommendation,
		staleTime: 5 * 60 * 1000,
	});
}

export { RECOMMENDATIONS_QUERY_KEY, useLatestRecommendationQuery };
