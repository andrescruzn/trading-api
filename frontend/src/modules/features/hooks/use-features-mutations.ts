import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	createFeatureSet,
	type FeatureSetInput,
} from '@/modules/features/api/features.api';
import { FEATURE_SETS_QUERY_KEY } from '@/modules/features/hooks/use-features-queries';

function useCreateFeatureSetMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: FeatureSetInput) => createFeatureSet(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: FEATURE_SETS_QUERY_KEY }),
	});
}

export { useCreateFeatureSetMutation };
