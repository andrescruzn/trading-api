import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
	type CandleFeatureFilters,
	listCandleFeatures,
	listFeatureSets,
} from '@/modules/features/api/features.api';

const FEATURE_SETS_QUERY_KEY = ['feature-sets'] as const;
const CANDLE_FEATURES_QUERY_KEY = ['candle-features'] as const;

function useFeatureSetsQuery() {
	return useQuery({
		queryKey: FEATURE_SETS_QUERY_KEY,
		queryFn: listFeatureSets,
		staleTime: 5 * 60 * 1000,
	});
}

/** Solo consulta cuando hay símbolo y timeframe elegidos. */
function useCandleFeaturesQuery(filters: Partial<CandleFeatureFilters>) {
	const { symbol_id, timeframe_id, feature_set_id, limit } = filters;
	return useQuery({
		queryKey: [
			...CANDLE_FEATURES_QUERY_KEY,
			{ symbol_id, timeframe_id, feature_set_id, limit },
		],
		queryFn: () =>
			listCandleFeatures({
				symbol_id: symbol_id as number,
				timeframe_id: timeframe_id as number,
				feature_set_id,
				limit,
			}),
		enabled: !!symbol_id && !!timeframe_id,
		placeholderData: keepPreviousData,
	});
}

export {
	CANDLE_FEATURES_QUERY_KEY,
	FEATURE_SETS_QUERY_KEY,
	useCandleFeaturesQuery,
	useFeatureSetsQuery,
};
