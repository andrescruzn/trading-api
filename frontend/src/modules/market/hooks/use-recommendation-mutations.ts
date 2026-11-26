import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { AssetClass } from '@/modules/market/api/market.api';
import { generateMarketRecommendations } from '@/modules/market/api/recommendations.api';
import { RECOMMENDATIONS_QUERY_KEY } from '@/modules/market/hooks/use-recommendation-queries';

function useGenerateRecommendationsMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: { asset_class?: AssetClass }) =>
			generateMarketRecommendations(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: RECOMMENDATIONS_QUERY_KEY }),
	});
}

export { useGenerateRecommendationsMutation };
