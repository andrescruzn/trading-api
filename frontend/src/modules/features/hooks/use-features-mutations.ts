import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	type CalculateFeaturesInput,
	calculateFeatures,
	createFeatureSet,
	type FeatureSetInput,
} from '@/modules/features/api/features.api';
import {
	CANDLE_FEATURES_QUERY_KEY,
	FEATURE_SETS_QUERY_KEY,
} from '@/modules/features/hooks/use-features-queries';

function useCreateFeatureSetMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: FeatureSetInput) => createFeatureSet(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: FEATURE_SETS_QUERY_KEY }),
	});
}

function useCalculateFeaturesMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: CalculateFeaturesInput) => calculateFeatures(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: CANDLE_FEATURES_QUERY_KEY }),
	});
}

export { useCalculateFeaturesMutation, useCreateFeatureSetMutation };
