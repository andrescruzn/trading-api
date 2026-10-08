import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	createStrategy,
	type StrategyInput,
	type StrategyUpdate,
	updateStrategy,
} from '@/modules/strategies/api/strategies.api';
import { STRATEGIES_QUERY_KEY } from '@/modules/strategies/hooks/use-strategies-queries';

// La key base cubre la lista y el detalle (`['strategies', id]`).
function useCreateStrategyMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: StrategyInput) => createStrategy(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: STRATEGIES_QUERY_KEY }),
	});
}

function useUpdateStrategyMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({ id, input }: { id: number; input: StrategyUpdate }) =>
			updateStrategy(id, input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: STRATEGIES_QUERY_KEY }),
	});
}

export { useCreateStrategyMutation, useUpdateStrategyMutation };
